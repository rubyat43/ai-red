# app/api/routes/agent_versions.py
# Purpose: Endpoints to list and register agent candidate versions.

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import AgentVersionModel
from app.schemas.schemas import AgentVersionCreate, AgentVersionResponse
from app.api.deps import verify_api_key_optional

router = APIRouter(prefix="/agent-versions", tags=["Agent Versions"])


@router.get("", response_model=List[AgentVersionResponse], summary="List Agent Versions")
def list_versions(db: Session = Depends(get_db)):
    """
    List all registered agent candidate versions with their configuration profiles.
    """
    records = db.query(AgentVersionModel).order_by(AgentVersionModel.id.asc()).all()
    results = []
    for r in records:
        allowed = [t.strip() for t in r.allowed_tools.split(",") if t.strip()]
        results.append(
            AgentVersionResponse(
                id=r.id,
                version_id=r.version_id,
                name=r.name,
                description=r.description or "",
                system_prompt=r.system_prompt,
                input_filter=r.input_filter,
                output_filter=r.output_filter,
                trust_tool_output=r.trust_tool_output,
                sanitize_memory=r.sanitize_memory,
                allowed_tools=allowed,
                created_at=r.created_at,
            )
        )
    return results


@router.post("", response_model=AgentVersionResponse, status_code=status.HTTP_201_CREATED, summary="Register Agent Version")
def create_version(
    payload: AgentVersionCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key_optional),
):
    """
    Register a new candidate agent version.
    """
    existing = db.query(AgentVersionModel).filter(AgentVersionModel.version_id == payload.version_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent version '{payload.version_id}' already exists",
        )

    tools_str = ",".join(payload.allowed_tools)
    model = AgentVersionModel(
        version_id=payload.version_id,
        name=payload.name,
        description=payload.description or "",
        system_prompt=payload.system_prompt,
        input_filter=payload.input_filter,
        output_filter=payload.output_filter,
        trust_tool_output=payload.trust_tool_output,
        sanitize_memory=payload.sanitize_memory,
        allowed_tools=tools_str,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    return AgentVersionResponse(
        id=model.id,
        version_id=model.version_id,
        name=model.name,
        description=model.description or "",
        system_prompt=model.system_prompt,
        input_filter=model.input_filter,
        output_filter=model.output_filter,
        trust_tool_output=model.trust_tool_output,
        sanitize_memory=model.sanitize_memory,
        allowed_tools=payload.allowed_tools,
        created_at=model.created_at,
    )
