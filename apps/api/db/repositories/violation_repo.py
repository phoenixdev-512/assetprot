import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.asset import Asset
from models.violation import Violation


async def list_by_org(
    db: AsyncSession, org_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> tuple[list[Violation], int]:
    base = select(Violation).join(Asset, Violation.asset_id == Asset.id).where(Asset.org_id == org_id)
    count_q = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_q.scalar_one()
    q = await db.execute(base.offset(offset).limit(limit))
    return list(q.scalars().all()), total


async def create(
    db: AsyncSession,
    asset_id: uuid.UUID,
    discovered_url: str,
    platform: str,
    confidence: float,
    status: str = "suspected",
    infringement_type: str | None = None,
    estimated_reach: int | None = None,
    rights_territory_violation: bool = False,
) -> Violation:
    violation = Violation(
        asset_id=asset_id,
        discovered_url=discovered_url,
        platform=platform,
        confidence=confidence,
        status=status,
        infringement_type=infringement_type,
        estimated_reach=estimated_reach,
        rights_territory_violation=rights_territory_violation,
    )
    db.add(violation)
    await db.commit()
    await db.refresh(violation)
    return violation