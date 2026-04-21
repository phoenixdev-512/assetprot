import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_org_id
from schemas.asset import AssetResponse
from schemas.base import APIResponse, PaginatedResponse
from services.asset_service import get_asset, list_assets

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("", response_model=PaginatedResponse[AssetResponse])
async def list_assets_route(
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    assets, total = await list_assets(db, org_id, offset, limit)
    return PaginatedResponse(
        success=True,
        data=[AssetResponse.model_validate(a) for a in assets],
        meta={"total": total, "offset": offset, "limit": limit},
    )


@router.get("/{asset_id}", response_model=APIResponse[AssetResponse])
async def get_asset_route(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    asset = await get_asset(db, asset_id, org_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return APIResponse(success=True, data=AssetResponse.model_validate(asset))
