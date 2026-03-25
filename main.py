"""Application entrypoint for AgriTriageAgent FastAPI service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.database.db import init_db
from app.utils.config import get_settings
from app.utils.logging import configure_logging, get_logger


settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Run startup and shutdown hooks for the API service."""
    logger.info("Starting %s in %s mode.", settings.app_name, settings.app_env)
    init_db()
    yield
    logger.info("Shutting down %s.", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log request lifecycle, response code, errors, and response time."""
    start_time = perf_counter()
    client_host = request.client.host if request.client else "unknown"

    logger.info(
        "Incoming request method=%s path=%s client=%s",
        request.method,
        request.url.path,
        client_host,
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - start_time) * 1000
        logger.exception(
            "Unhandled error method=%s path=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    duration_ms = (perf_counter() - start_time) * 1000
    logger.info(
        "Completed request method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
    return response


app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    """Return API availability metadata."""
    return {"message": "AgriTriageAgent API is running"}
