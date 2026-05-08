import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import redis as redis_lib
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from core.config import settings
from core.logging import setup_logging
from db.session import AsyncSessionLocal
from middleware.rate_limit import RateLimitMiddleware
from middleware.request_context import RequestContextMiddleware
from routers.assets import router as assets_router
from routers.auth import router as auth_router
from routers.scan_runs import router as scan_runs_router
from routers.tasks import router as tasks_router
from routers.violations import router as violations_router
from routers.dmca import router as dmca_router
from routers.ws import router as ws_router
from routers.threats import router as threats_router

# Configure structured logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


def _ensure_upload_dir() -> str:
    """Ensure upload directory exists and is writable."""
    upload_dir = Path(settings.upload_dir)
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        test_file = upload_dir / ".writetest"
        test_file.write_text("test")
        test_file.unlink()
        logger.info(f"Upload directory ready: {upload_dir.absolute()}")
        return str(upload_dir.absolute())
    except Exception as e:
        logger.error(f"Upload directory setup failed: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_upload_dir()

    # Create database tables (ensures schema exists before seeding)
    try:
        from db.seed import create_tables
        await create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database table creation failed: {e}")

    # Load ML models (optional — demo works without them)
    if settings.app_env != "test":
        try:
            from ml.model_loader import load_models
            load_models(app)
            logger.info("ML models loaded successfully")
        except Exception as e:
            logger.warning(f"ML models not loaded (demo will use seed data): {e}")

    # Auto-seed demo data if configured
    if os.getenv("SEED_DEMO_DATA", "").lower() == "true":
        try:
            from db.seed import seed_demo_data
            await seed_demo_data()
            logger.info("Demo data seeded successfully")
        except Exception as e:
            logger.warning(f"Demo data seeding skipped: {e}")

    yield


app = FastAPI(title="GUARDIAN API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
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
app.include_router(threats_router)


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

    # Upload directory
    try:
        upload_path = Path(settings.upload_dir)
        if upload_path.exists() and upload_path.is_dir():
            services["upload_dir"] = {"status": "ok", "path": str(upload_path)}
        else:
            services["upload_dir"] = {"status": "error", "message": "Directory not found"}
    except Exception as e:
        services["upload_dir"] = {"status": "error", "message": str(e)}

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
                "version": "0.1.0",
                "services": services,
            },
            "meta": {},
        },
    )
