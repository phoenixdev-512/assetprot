import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import db.repositories.violation_repo as violation_repo


async def list_violations(db: AsyncSession, org_id: uuid.UUID, offset: int, limit: int):
    return await violation_repo.list_by_org(db, org_id, offset, limit)
