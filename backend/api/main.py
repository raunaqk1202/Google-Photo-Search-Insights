"""
Discovery Engine API — FastAPI Application Entrypoint.

AI-Powered User Discovery Engine for Google Photos Retrieval.
"""

import logging
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.database import engine, Base
from api.routers import health, chat, scrape, citations, data

settings = get_settings()

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    logger.info("Starting Discovery Engine API (env=%s)", settings.app_env)

    # Create tables if they don't exist (dev convenience; prod uses Alembic)
    if settings.app_env == "development":
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")

    yield

    logger.info("Shutting down Discovery Engine API")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="AI-Powered User Discovery Engine analyzing Google Photos retrieval failures under incomplete memory.",
    lifespan=lifespan,
)

# Ensure wildcard is not used with allow_credentials=True in production
cors_origins = settings.cors_origins_list
allow_credentials = True
if settings.app_env == "production" and "*" in cors_origins:
    logger.warning("Wildcard CORS origin is insecure in production. Disabling credentials.")
    allow_credentials = False
    cors_origins = ["*"]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# Register routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(scrape.router, prefix="/api/v1")
app.include_router(citations.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — API info."""
    return {
        "name": settings.app_title,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
