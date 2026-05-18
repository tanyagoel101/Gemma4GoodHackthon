from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.config import get_settings
from backend.database import engine, init_db
from backend.routers import clinician, patients, prompts, recordings, reports, sessions
from backend.schemas import HealthStatus
from backend.services.gemma import check_ollama_health


settings = get_settings()
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recordings.router, prefix=settings.api_prefix)
app.include_router(patients.router, prefix=settings.api_prefix)
app.include_router(sessions.router, prefix=settings.api_prefix)
app.include_router(clinician.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(prompts.router, prefix=settings.api_prefix)


@app.middleware("http")
async def upload_request_trace(request: Request, call_next):
    if request.url.path in {f"{settings.api_prefix}/recordings/upload", f"{settings.api_prefix}/recordings/upload-blob"}:
        started_at = perf_counter()
        logger.info(
            "Upload HTTP request started content_length=%s content_type=%s",
            request.headers.get("content-length", "unknown"),
            request.headers.get("content-type", "unknown"),
        )
        response = await call_next(request)
        logger.info(
            "Upload HTTP request finished status=%s elapsed_ms=%.0f",
            response.status_code,
            (perf_counter() - started_at) * 1000,
        )
        return response
    return await call_next(request)


@app.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "ready"
    except SQLAlchemyError as exc:
        return HealthStatus(
            status="degraded",
            database="unreachable",
            ollama="unknown",
            model="unknown",
            message=f"Database is not available: {exc}",
        )

    ollama_status, detail = await check_ollama_health()
    if ollama_status == "ready":
        return HealthStatus(
            status="ok",
            database=db_status,
            ollama="reachable",
            model=settings.ollama_model,
            message="VoiceTrace is ready. All data stays on this device.",
        )
    if ollama_status == "fallback":
        return HealthStatus(
            status="degraded",
            database=db_status,
            ollama="reachable",
            model=detail,
            message=f"Ollama is reachable, but `{settings.ollama_model}` is missing. Run `ollama pull {settings.ollama_model}`.",
        )
    if ollama_status == "missing_model":
        return HealthStatus(
            status="degraded",
            database=db_status,
            ollama="reachable",
            model="missing",
            message=(
                f"Ollama is running but `{settings.ollama_model}` is not installed. "
                f"Run `ollama pull {settings.ollama_model}`. Available: {detail}."
            ),
        )
    return HealthStatus(
        status="degraded",
        database=db_status,
        ollama="unreachable",
        model="unknown",
        message=(
            f"VoiceTrace could not reach Ollama at {settings.ollama_base_url}. "
            f"Start Ollama and run `ollama pull {settings.ollama_model}`. Details: {detail}"
        ),
    )
