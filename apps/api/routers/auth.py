from fastapi import APIRouter, Depends

from dependencies.auth import get_auth_service, get_current_user
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from services.auth_service import AuthService

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    data = await service.register(req)
    return {"success": True, "data": data.model_dump(), "meta": {}}


@router.post("/login")
async def login(req: LoginRequest, service: AuthService = Depends(get_auth_service)):
    data = await service.login(req)
    return {"success": True, "data": data.model_dump(), "meta": {}}


@router.post("/refresh")
async def refresh(req: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    data = await service.refresh(req)
    return {"success": True, "data": data.model_dump(), "meta": {}}


@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    data = await service.get_me(str(current_user.id))
    return {"success": True, "data": data.model_dump(), "meta": {}}
