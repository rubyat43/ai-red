# app/api/routes/settings.py
# Purpose: Endpoints to inspect and update risk calculation weights and thresholds.

import json
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.schemas.schemas import SettingsPayload
from app.models.entities import SettingsSnapshotModel
from app.api.deps import verify_api_key_optional

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsPayload, summary="Get Risk Weights and Thresholds")
def get_settings():
    """
    Returns current active evaluation weights, thresholds, and execution modes.
    """
    return SettingsPayload(
        risk_threshold=settings.risk_threshold,
        max_response_time_ms=settings.max_response_time_ms,
        risk_weights=settings.risk_weights,
        critical_rules=settings.critical_rules,
        llm_mode=settings.llm_mode,
        deployment_driver=settings.deployment_driver,
    )


@router.put("", response_model=SettingsPayload, summary="Update Risk Weights and Thresholds")
def update_settings(
    payload: SettingsPayload,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key_optional),
):
    """
    Update risk thresholds and weights, persisting a snapshot to the database.
    """
    if payload.risk_threshold is not None:
        settings.risk_threshold = payload.risk_threshold
    if payload.max_response_time_ms is not None:
        settings.max_response_time_ms = payload.max_response_time_ms
    if payload.risk_weights:
        settings.risk_weights.update(payload.risk_weights)
    if payload.critical_rules:
        settings.critical_rules.update(payload.critical_rules)

    # Save snapshot
    snapshot = SettingsSnapshotModel(
        risk_threshold=settings.risk_threshold,
        risk_weights_json=json.dumps(settings.risk_weights),
        critical_rules_json=json.dumps(settings.critical_rules),
        created_at=datetime.utcnow(),
    )
    db.add(snapshot)
    db.commit()

    return SettingsPayload(
        risk_threshold=settings.risk_threshold,
        max_response_time_ms=settings.max_response_time_ms,
        risk_weights=settings.risk_weights,
        critical_rules=settings.critical_rules,
        llm_mode=settings.llm_mode,
        deployment_driver=settings.deployment_driver,
    )
