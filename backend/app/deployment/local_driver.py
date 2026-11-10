# app/deployment/local_driver.py
# Purpose: Local in-process Blue/Green deployment driver for zero-cloud desktop execution.

from typing import Dict, Any
from datetime import datetime
from app.deployment.base_driver import DeploymentDriver
from app.database import SessionLocal
from app.models.entities import DeploymentStateModel


class LocalDriver(DeploymentDriver):
    """
    Simulates Blue/Green deployment and router state using SQLite database persistence.
    """

    def _get_or_create_state(self) -> DeploymentStateModel:
        with SessionLocal() as db:
            state = db.query(DeploymentStateModel).first()
            if not state:
                state = DeploymentStateModel(
                    active_color="blue",
                    blue_version="v1.0.0",
                    green_version="v2.0.0",
                    blue_traffic_percent=100,
                    green_traffic_percent=0,
                    last_switch_at=datetime.utcnow(),
                    notes="Initialized local deployment state"
                )
                db.add(state)
                db.commit()
                db.refresh(state)
            return state

    def deploy_green(self, version: str) -> str:
        with SessionLocal() as db:
            state = db.query(DeploymentStateModel).first()
            if not state:
                state = self._get_or_create_state()
            state.green_version = version
            state.green_traffic_percent = 0
            state.notes = f"Candidate version {version} deployed to Green (isolated, 0% traffic)"
            db.commit()
        return "local://agent-green"

    def promote_green(self) -> None:
        with SessionLocal() as db:
            state = db.query(DeploymentStateModel).first()
            if state:
                previous_active = state.active_color
                # Traffic switches from Blue to Green
                state.active_color = "green"
                state.blue_traffic_percent = 0
                state.green_traffic_percent = 100
                state.last_switch_at = datetime.utcnow()
                state.notes = f"Promoted Green ({state.green_version}) to live production. Blue ({state.blue_version}) stood down."
                db.commit()

    def rollback_to_blue(self) -> None:
        with SessionLocal() as db:
            state = db.query(DeploymentStateModel).first()
            if state:
                # Keep or revert all traffic to Blue
                state.active_color = "blue"
                state.blue_traffic_percent = 100
                state.green_traffic_percent = 0
                state.last_switch_at = datetime.utcnow()
                state.notes = f"Green ({state.green_version}) failed security checks. Rolled back: 100% traffic retained on Blue ({state.blue_version})."
                db.commit()

    def get_state(self) -> Dict[str, Any]:
        with SessionLocal() as db:
            state = db.query(DeploymentStateModel).first()
            if not state:
                state = self._get_or_create_state()
            return {
                "active_color": state.active_color,
                "blue_version": state.blue_version,
                "green_version": state.green_version,
                "blue_traffic_percent": state.blue_traffic_percent,
                "green_traffic_percent": state.green_traffic_percent,
                "last_switch_at": state.last_switch_at,
                "notes": state.notes,
            }
