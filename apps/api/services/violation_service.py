import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import db.repositories.violation_repo as violation_repo


async def list_violations(
    db: AsyncSession, org_id: uuid.UUID, offset: int, limit: int, asset_id: uuid.UUID | None = None
):
    return await violation_repo.list_by_org(db, org_id, offset, limit, asset_id)


async def get_violation(db: AsyncSession, violation_id: uuid.UUID, org_id: uuid.UUID):
    return await violation_repo.get_by_id(db, violation_id, org_id)
