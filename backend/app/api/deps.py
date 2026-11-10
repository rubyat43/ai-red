# app/api/deps.py
# Purpose: Shared dependencies including database session injection and optional API key check.

from typing import Generator, Optional
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings


def verify_api_key_optional(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Optional API key check for write operations in development mode.
    """
    if settings.environment == "production" and x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
    return True
