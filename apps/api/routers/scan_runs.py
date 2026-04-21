import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_org_id, get_db
from schemas.base import PaginatedResponse
from schemas.scan_run import ScanRunResponse
from services.scan_run_service import list_scan_runs

router = APIRouter(prefix="/api/v1/scan-runs", tags=["scan-runs"])


@router.get("", response_model=PaginatedResponse[ScanRunResponse])
async def list_scan_runs_route(
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    runs, total = await list_scan_runs(db, org_id, offset, limit)
    return PaginatedResponse(
        success=True,
        data=[ScanRunResponse.model_validate(r) for r in runs],
        meta={"total": total, "offset": offset, "limit": limit},
    )
