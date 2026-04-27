import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal
from ml.agents.state import AgentState
from models.asset import Asset


async def planner_node(state: AgentState) -> dict[str, Any]:
    asset_id = state["asset_id"]
    org_id = state["org_id"]

    search_tasks = []

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Asset).where(Asset.id == uuid.UUID(asset_id), Asset.org_id == uuid.UUID(org_id))
        )
        asset = result.scalar_one_or_none()

        if asset is None:
            state["errors"].append({
                "node": "planner",
                "error": f"Asset {asset_id} not found",
            })
            return {"search_tasks": [], "errors": state["errors"]}

        title = asset.title
        metadata = asset.rights_metadata or {}
        teams = metadata.get("teams", [])
        sport = metadata.get("sport", "")
        tags = metadata.get("tags", [])

        search_queries = [title]
        if teams:
            search_queries.extend(teams)
        if sport:
            search_queries.append(sport)
        if tags:
            search_queries.extend(tags)

        for query in search_queries[:10]:
            search_tasks.append({
                "type": "text_search",
                "query": query,
                "platform": "google",
            })
            search_tasks.append({
                "type": "text_search",
                "query": query,
                "platform": "twitter",
            })
            search_tasks.append({
                "type": "text_search",
                "query": query,
                "platform": "reddit",
            })

        search_tasks.append({
            "type": "image_search",
            "asset_id": asset_id,
            "platform": "google",
        })

    return {"search_tasks": search_tasks}