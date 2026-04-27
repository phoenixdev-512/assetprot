import logging
from typing import Any

import uuid

from db.repositories.violation_repo import create as create_violation
from db.session import AsyncSessionLocal
from ml.agents.state import AgentState

logger = logging.getLogger(__name__)


async def reporter_node(state: AgentState) -> dict[str, Any]:
    confirmed_violations = state.get("confirmed_violations", [])
    errors = state.get("errors", [])

    violations_written = []

    async with AsyncSessionLocal() as db:
        for violation_data in confirmed_violations:
            try:
                asset_id = uuid.UUID(violation_data["asset_id"])
                violation = await create_violation(
                    db,
                    asset_id=asset_id,
                    discovered_url=violation_data["url"],
                    platform=violation_data.get("platform", "unknown"),
                    confidence=violation_data.get("confidence", 0.5),
                    status="confirmed" if violation_data.get("confidence", 0) > 0.8 else "suspected",
                    infringement_type=violation_data.get("detection_type"),
                    estimated_reach=violation_data.get("estimated_reach"),
                    rights_territory_violation=False,
                )
                violations_written.append(str(violation.id))
            except Exception as e:
                logger.error(f"Failed to write violation: {e}")
                errors.append({
                    "node": "reporter",
                    "error": str(e),
                })

    return {"status": "completed", "violations_written": violations_written, "errors": errors}