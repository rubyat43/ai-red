# app/api/routes/validation_runs.py
# Purpose: Endpoints to launch, list, and monitor AI Red Team validation runs.

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import ValidationRunModel, AttackResultModel, TaskResultModel
from app.schemas.schemas import (
    ValidationRunCreate,
    ValidationRunResponse,
    ValidationRunDetail,
    AttackResultSchema,
    TaskResultSchema,
)
from app.services.validation_service import ValidationService
from app.api.deps import verify_api_key_optional

router = APIRouter(prefix="/validation-runs", tags=["Validation Runs"])


def _serialize_run(run: ValidationRunModel) -> dict:
    try:
        metrics = json.loads(run.metrics_json or "{}")
    except Exception:
        metrics = {}
    try:
        reasons = json.loads(run.reasons_json or "[]")
    except Exception:
        reasons = []

    return {
        "id": run.id,
        "version_id": run.version_id,
        "status": run.status,
        "attacks_total": run.attacks_total,
        "attacks_done": run.attacks_done,
        "current_step": run.current_step,
        "risk_score": run.risk_score,
        "decision": run.decision,
        "metrics": metrics,
        "reasons": reasons,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


@router.post("", response_model=ValidationRunResponse, status_code=status.HTTP_202_ACCEPTED, summary="Start Validation Run")
def start_validation_run(
    payload: ValidationRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key_optional),
):
    """
    Initiate an automated AI Red Team validation run against the target Green candidate version.
    The run executes asynchronously in the background.
    """
    new_run = ValidationRunModel(
        version_id=payload.version_id,
        status="pending",
        attacks_total=15,  # Estimated total attacks
        attacks_done=0,
        current_step="Queued for validation",
        decision="PENDING",
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # Launch in background worker
    background_tasks.add_task(ValidationService.execute_validation_job, new_run.id)

    return _serialize_run(new_run)


@router.get("", response_model=List[ValidationRunResponse], summary="List Validation Runs")
def list_validation_runs(db: Session = Depends(get_db)):
    """
    Retrieve all historical and active validation runs.
    """
    runs = db.query(ValidationRunModel).order_by(ValidationRunModel.id.desc()).all()
    return [_serialize_run(r) for r in runs]


@router.get("/{run_id}", response_model=ValidationRunDetail, summary="Get Validation Run Detail")
def get_validation_run(run_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full details of a specific validation run, including metrics, decision, and attack logs.
    """
    run = db.query(ValidationRunModel).filter(ValidationRunModel.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation run #{run_id} not found",
        )

    base_data = _serialize_run(run)

    attack_records = (
        db.query(AttackResultModel)
        .filter(AttackResultModel.run_id == run_id)
        .order_by(AttackResultModel.id.asc())
        .all()
    )
    task_records = (
        db.query(TaskResultModel)
        .filter(TaskResultModel.run_id == run_id)
        .order_by(TaskResultModel.id.asc())
        .all()
    )

    attack_schemas = [
        AttackResultSchema(
            id=a.id,
            attack_name=a.attack_name,
            category=a.category,
            severity=a.severity,
            prompt=a.prompt,
            agent_reply=a.agent_reply,
            is_success=a.is_success,
            canary_leak=a.canary_leak,
            privilege_escalation=a.privilege_escalation,
            tool_misuse=a.tool_misuse,
            policy_violation=a.policy_violation,
            latency_ms=a.latency_ms,
            notes=a.notes,
        )
        for a in attack_records
    ]

    task_schemas = [
        TaskResultSchema(
            id=t.id,
            task_id=t.task_id,
            prompt=t.prompt,
            agent_reply=t.agent_reply,
            is_success=t.is_success,
            latency_ms=t.latency_ms,
        )
        for t in task_records
    ]

    return ValidationRunDetail(
        **base_data,
        attack_results=attack_schemas,
        task_results=task_schemas,
    )
