from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="GUARDIAN API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/health")
async def health():
    return {"success": True, "data": {"status": "ok"}, "meta": {}}
