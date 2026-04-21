import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import db.repositories.asset_repo as asset_repo
from models.asset import Asset


async def list_assets(db: AsyncSession, org_id: uuid.UUID, offset: int, limit: int):
    return await asset_repo.list_by_org(db, org_id, offset, limit)


async def get_asset(db: AsyncSession, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset | None:
    return await asset_repo.get_by_id(db, asset_id, org_id)
