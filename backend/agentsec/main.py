from __future__ import annotations

import hmac
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import SessionLocal, migrate_db
from .logging_config import configure_logging
from .models import Scenario
from .routers import audits, connectors, findings, projects, rag, system
from .services.scenarios import SCENARIOS

settings = get_settings()
configure_logging(settings)
log = structlog.get_logger(__name__)


def seed_scenarios() -> None:
    with SessionLocal() as db:
        for item in SCENARIOS:
            if db.get(Scenario, (item["id"], item["version"])):
                continue
            db.add(
                Scenario(
                    id=item["id"],
                    version=item["version"],
                    name=item["name"],
                    description=item["description"],
                    category=item["category"],
                    prerequisites={},
                    configuration={},
                    procedure=[{"type": "chat", "template": item["template"]}],
                    success_criteria={"marker_disclosed": False, "tool_calls_attempted": False},
                    failure_criteria={"marker_disclosed": True},
                    expected_marker="{marker}",
                    references=item["references"],
                )
            )
        db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    migrate_db()
    seed_scenarios()
    log.info("backend_started", host=settings.host, port=settings.port, version=settings.version)
    try:
        yield
    finally:
        log.info("backend_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def local_auth(request: Request, call_next):
    # CORS preflight carries no bearer token. The CORS middleware still limits the
    # permitted origins, methods and headers before the authenticated request.
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path in {"/health", "/api/v1/version"}:
        return await call_next(request)
    if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        return JSONResponse({"detail": "Local clients only"}, status_code=403)
    supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not settings.api_token or not hmac.compare_digest(supplied, settings.api_token):
        return JSONResponse({"detail": "Invalid local API token"}, status_code=401)
    return await call_next(request)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentsec-backend", "version": settings.version}


@app.get("/api/v1/version")
async def version() -> dict[str, str]:
    return {"version": settings.version}


app.include_router(projects.router, prefix="/api/v1")
app.include_router(findings.router, prefix="/api/v1")
app.include_router(audits.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(connectors.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")
