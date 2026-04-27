import asyncio
import hashlib
import logging
from typing import Any
from urllib.parse import urljoin

import httpx
from redis import Redis

from config.crawl_targets import CRAWL_TARGETS, get_target
from core.config import settings
from ml.agents.state import AgentState

logger = logging.getLogger(__name__)

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

PLAYWRIGHT_BROWSER = None


async def get_playwright_browser():
    global PLAYWRIGHT_BROWSER
    if PLAYWRIGHT_BROWSER is None:
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        PLAYWRIGHT_BROWSER = await pw.chromium.launch(headless=True)
    return PLAYWRIGHT_BROWSER


def check_url_dedup(url: str) -> bool:
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    key = f"crawl:url:{url_hash}"
    if redis_client.exists(key):
        return False
    redis_client.setex(key, 86400, "1")
    return True


def check_rate_limit(domain: str) -> bool:
    target = get_target(domain)
    if not target:
        return False
    key = f"rate:{domain}"
    current = redis_client.get(key)
    if current is None:
        redis_client.setex(key, 60, "1")
        return True
    if int(current) >= target.rate_limit_per_minute:
        return False
    redis_client.incr(key)
    return True


async def fetch_with_httpx(url: str) -> list[str]:
    discovered = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                for img in soup.find_all("img"):
                    src = img.get("src") or img.get("data-src")
                    if src and src.startswith("http"):
                        if check_url_dedup(src):
                            discovered.append(src)
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("http"):
                        if check_url_dedup(href):
                            discovered.append(href)
    except Exception as e:
        logger.error(f"httpx fetch error for {url}: {e}")
    return discovered


async def fetch_with_playwright(url: str) -> list[str]:
    discovered = []
    try:
        browser = await get_playwright_browser()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        elements = await page.query_selector_all("img")
        for el in elements:
            src = await el.get_attribute("src")
            if src and src.startswith("http"):
                if check_url_dedup(src):
                    discovered.append(src)

        links = await page.query_selector_all("a[href]")
        for link in links:
            href = await link.get_attribute("href")
            if href and href.startswith("http"):
                if check_url_dedup(href):
                    discovered.append(href)

        await page.close()
    except Exception as e:
        logger.error(f"Playwright fetch error for {url}: {e}")
    return discovered


async def crawler_node(state: AgentState) -> dict[str, Any]:
    search_tasks = state.get("search_tasks", [])
    discovered_urls: list[str] = []
    errors = state.get("errors", [])

    tasks_by_platform: dict[str, list[dict]] = {}
    for task in search_tasks:
        platform = task.get("platform", "google")
        if platform not in tasks_by_platform:
            tasks_by_platform[platform] = []
        tasks_by_platform[platform].append(task)

    for platform, tasks in tasks_by_platform.items():
        target = get_target(platform)
        if not target:
            continue

        for task in tasks[:5]:
            query = task.get("query", "")
            if not query:
                continue

            if not check_rate_limit(platform):
                errors.append({
                    "node": "crawler",
                    "error": f"Rate limited for {platform}",
                })
                continue

            search_endpoint = target.search_endpoint or ""
            url = f"{target.base_url}{search_endpoint.format(query=query)}"

            if target.requires_js:
                urls = await fetch_with_playwright(url)
            else:
                urls = await fetch_with_httpx(url)

            discovered_urls.extend(urls)

            await asyncio.sleep(1)

    return {"discovered_urls": discovered_urls, "errors": errors}