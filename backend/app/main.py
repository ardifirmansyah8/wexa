"""FastAPI application entrypoint.

Wires up CORS, a global handler that turns a `DatabaseUnavailable` into a clean
503 (so the frontend can render a friendly state instead of a stack trace), and
the API routes.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import DatabaseUnavailable, close_driver, verify_connectivity
from .routers import api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moviegraph")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    # Release the shared driver's connection pool on shutdown.
    close_driver()


app = FastAPI(
    title="MovieGraph API",
    version="1.0.0",
    description="A graph-native movie recommendation service backed by CognoDB.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(DatabaseUnavailable)
async def db_unavailable_handler(_: Request, exc: DatabaseUnavailable) -> JSONResponse:
    """Any query that cannot reach CognoDB surfaces here as a 503."""
    logger.warning("Serving 503 — database unavailable: %s", exc)
    return JSONResponse(
        status_code=503,
        content={
            "error": "database_unavailable",
            "message": "The movie graph is temporarily unreachable. Please try again shortly.",
        },
    )


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    """Friendly landing for anyone who opens the API host directly — this is the
    backend, not the app. Points to the health check and interactive docs."""
    return {
        "service": "MovieGraph API",
        "status": "ok",
        "health": "/api/health",
        "docs": "/docs",
        "app": "https://moviegraph.vercel.app",
    }


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, object]:
    """Liveness + database reachability, used by the frontend to detect outages."""
    configured = settings.is_configured
    reachable = False
    if configured:
        try:
            verify_connectivity()
            reachable = True
        except DatabaseUnavailable:
            reachable = False
    return {"status": "ok", "configured": configured, "database": reachable}


app.include_router(api.router, prefix="/api")
