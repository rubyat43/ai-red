# app/api/routes/experiments.py
# Purpose: Endpoints for running and reviewing scientific baseline-vs-proposed validation experiments.

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import ExperimentModel
from app.schemas.schemas import ExperimentCreate, ExperimentResponse
from app.services.experiment_service import ExperimentService
from app.api.deps import verify_api_key_optional

router = APIRouter(prefix="/experiments", tags=["Experiments"])


def _serialize_experiment(exp: ExperimentModel) -> ExperimentResponse:
    return ExperimentResponse(
        id=exp.id,
        title=exp.title,
        baseline_results=json.loads(exp.baseline_results_json or "[]"),
        proposed_results=json.loads(exp.proposed_results_json or "[]"),
        summary=json.loads(exp.summary_json or "{}"),
        created_at=exp.created_at,
    )


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED, summary="Run Comparative Benchmark")
def run_experiment(
    payload: ExperimentCreate,
    _: bool = Depends(verify_api_key_optional),
):
    """
    Run baseline vs proposed red teaming experiment comparing deployment accuracy and risk prevention.
    """
    result = ExperimentService.run_comparative_experiment(rounds=payload.rounds)
    with get_db() as db:
        pass  # Just ensure db can be obtained if needed
    from app.database import SessionLocal
    with SessionLocal() as db:
        exp = db.query(ExperimentModel).filter(ExperimentModel.id == result["id"]).first()
        if not exp:
            raise HTTPException(status_code=500, detail="Experiment record creation failed")
        return _serialize_experiment(exp)


@router.get("", response_model=List[ExperimentResponse], summary="List Experiments")
def list_experiments(db: Session = Depends(get_db)):
    """
    List past comparative experiments.
    """
    exps = db.query(ExperimentModel).order_by(ExperimentModel.id.desc()).all()
    return [_serialize_experiment(e) for e in exps]


@router.get("/{experiment_id}", response_model=ExperimentResponse, summary="Get Experiment Detail")
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """
    Retrieve benchmark details for a specific experiment ID.
    """
    exp = db.query(ExperimentModel).filter(ExperimentModel.id == experiment_id).first()
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment #{experiment_id} not found",
        )
    return _serialize_experiment(exp)
