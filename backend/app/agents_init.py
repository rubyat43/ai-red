# app/agents_init.py
# Purpose: Seeds default versions and initializes initial deployment state if database is fresh.

from datetime import datetime
from app.database import SessionLocal
from app.models.entities import AgentVersionModel, DeploymentStateModel
from agents.target_agent.versions import PRESET_VERSIONS


def seed_default_versions():
    """
    Ensure preset agent versions and initial deployment records exist in the database.
    """
    with SessionLocal() as db:
        # Seed default agent versions
        for version_id, cfg in PRESET_VERSIONS.items():
            existing = db.query(AgentVersionModel).filter(AgentVersionModel.version_id == version_id).first()
            if not existing:
                model = AgentVersionModel(
                    version_id=cfg.version_id,
                    name=cfg.name,
                    description=cfg.description,
                    system_prompt=cfg.system_prompt,
                    input_filter=cfg.input_filter,
                    output_filter=cfg.output_filter,
                    trust_tool_output=cfg.trust_tool_output,
                    sanitize_memory=cfg.sanitize_memory,
                    allowed_tools=",".join(cfg.allowed_tools),
                    created_at=datetime.utcnow(),
                )
                db.add(model)

        # Seed initial deployment state
        state = db.query(DeploymentStateModel).first()
        if not state:
            state = DeploymentStateModel(
                active_color="blue",
                blue_version="v1.0.0",
                green_version="v2.0.0",
                blue_traffic_percent=100,
                green_traffic_percent=0,
                last_switch_at=datetime.utcnow(),
                notes="Initial production state: Blue v1.0.0 serving all traffic.",
            )
            db.add(state)

        db.commit()
