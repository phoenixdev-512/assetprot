import logging
import uuid

from celery_app import celery

from db.session import AsyncSessionLocal
from ml.agents.graph import agent_graph
from ml.agents.state import AgentState
from models.scan_run import ScanRun

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3)
def detection_task(self, asset_id: str, org_id: str):
    scan_run = None

    async def create_scan_run() -> ScanRun:
        async with AsyncSessionLocal() as db:
            scan_run = ScanRun(
                asset_id=uuid.UUID(asset_id),
                status="running",
            )
            db.add(scan_run)
            await db.commit()
            await db.refresh(scan_run)
            return scan_run

    async def update_scan_run(scan_run: ScanRun, status: str, violations_found: int, errors: list[dict] | None = None):
        scan_run.status = status
        scan_run.violations_found = violations_found
        if errors:
            scan_run.errors = errors
        async with AsyncSessionLocal() as db:
            db.add(scan_run)
            await db.commit()

    try:
        import asyncio

        async def run_detection():
            nonlocal scan_run
            scan_run = await create_scan_run()

            initial_state: AgentState = {
                "asset_id": asset_id,
                "org_id": org_id,
                "search_tasks": [],
                "discovered_urls": [],
                "candidate_matches": [],
                "confirmed_violations": [],
                "errors": [],
                "status": "running",
            }

            result = agent_graph.invoke(initial_state)

            return result

        result = asyncio.run(run_detection())

        violations_count = len(result.get("confirmed_violations", []))
        errors = result.get("errors", [])

        if scan_run:
            import asyncio

            async def finish():
                await update_scan_run(
                    scan_run, "complete", violations_count, errors if errors else None
                )

            asyncio.run(finish())

        return {
            "asset_id": asset_id,
            "status": "complete",
            "violations_found": violations_count,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"Detection task failed for asset {asset_id}: {e}")
        if scan_run:
            try:
                import asyncio

                async def fail():
                    await update_scan_run(scan_run, "failed", 0, [{"error": str(e)}])

                asyncio.run(fail())
            except Exception:
                pass
        raise self.retry(exc=e, countdown=60)