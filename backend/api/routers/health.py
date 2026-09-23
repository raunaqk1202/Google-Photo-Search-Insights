"""Health check router."""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    System health check.

    Verifies database connectivity and returns service status.
    """
    status = {"status": "healthy", "database": "healthy", "version": "0.1.0"}

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        status["status"] = "degraded"
        status["database"] = "unhealthy"

    return status
