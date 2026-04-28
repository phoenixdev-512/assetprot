from contextlib import asynccontextmanager

import redis as redis_lib
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

import os

from core.config import settings
from db.session import AsyncSessionLocal
from middleware.rate_limit import RateLimitMiddleware
from routers.assets import router as assets_router
from routers.auth import router as auth_router
from routers.scan_runs import router as scan_runs_router
from routers.tasks import router as tasks_router
from routers.violations import router as violations_router
from routers.dmca import router as dmca_router
from routers.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    if settings.app_env != "test":
        from ml.model_loader import load_models
        load_models(app)
    yield


app = FastAPI(title="GUARDIAN API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        error = detail
    else:
        error = {"code": "ERROR", "message": str(detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": error},
    )


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(assets_router)
app.include_router(violations_router)
app.include_router(scan_runs_router)
app.include_router(tasks_router)
app.include_router(dmca_router)
app.include_router(ws_router)


@app.get("/health")
async def health(request: Request):
    from datetime import datetime

    services = {}

    # Database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        services["database"] = {"status": "ok"}
    except Exception as e:
        services["database"] = {"status": "error", "message": str(e)}

    # Redis
    try:
        r = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        r.ping()
        services["redis"] = {"status": "ok"}
    except Exception as e:
        services["redis"] = {"status": "error", "message": str(e)}

    # Qdrant
    try:
        if hasattr(request.app.state, "qdrant"):
            request.app.state.qdrant.get_collections()
            services["qdrant"] = {"status": "ok"}
        else:
            services["qdrant"] = {"status": "not_initialized"}
    except Exception as e:
        services["qdrant"] = {"status": "error", "message": str(e)}

    # ML Models
    try:
        if hasattr(request.app.state, "clip_model") and hasattr(request.app.state, "clip_processor"):
            services["ml_models"] = {
                "status": "ok",
                "models": ["CLIP"],
            }
        else:
            services["ml_models"] = {"status": "not_loaded"}
    except Exception as e:
        services["ml_models"] = {"status": "error", "message": str(e)}

    # Overall status
    all_ok = all(s.get("status") == "ok" for s in services.values())
    status_str = "healthy" if all_ok else "degraded"

    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "success": True,
            "data": {
                "status": status_str,
                "timestamp": datetime.utcnow().isoformat(),
                "services": services,
            },
            "meta": {},
        },
    )
