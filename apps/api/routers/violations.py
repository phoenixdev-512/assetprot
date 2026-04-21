import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_org_id, get_db
from schemas.base import PaginatedResponse
from schemas.violation import ViolationResponse
from services.violation_service import list_violations

router = APIRouter(prefix="/api/v1/violations", tags=["violations"])


@router.get("", response_model=PaginatedResponse[ViolationResponse])
async def list_violations_route(
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    violations, total = await list_violations(db, org_id, offset, limit)
    return PaginatedResponse(
        success=True,
        data=[ViolationResponse.model_validate(v) for v in violations],
        meta={"total": total, "offset": offset, "limit": limit},
    )
