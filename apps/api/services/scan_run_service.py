import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import db.repositories.scan_run_repo as scan_run_repo


async def list_scan_runs(db: AsyncSession, org_id: uuid.UUID, offset: int, limit: int):
    return await scan_run_repo.list_by_org(db, org_id, offset, limit)
