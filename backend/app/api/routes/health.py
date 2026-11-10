# app/api/routes/health.py
# Purpose: Health check endpoint.

from datetime import datetime
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="System Health Check")
def get_health():
    """
    Returns system operational health status.
    """
    return {
        "status": "ok",
        "service": "ai-redteam-bluegreen-api",
        "timestamp": datetime.utcnow().isoformat(),
    }
