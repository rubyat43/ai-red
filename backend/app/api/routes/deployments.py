# app/api/routes/deployments.py
# Purpose: Endpoints for monitoring Blue/Green deployment status and performing manual rollbacks.

from fastapi import APIRouter, Depends
from app.deployment import get_deployment_driver
from app.schemas.schemas import DeploymentStateResponse
from app.api.deps import verify_api_key_optional

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.get("/state", response_model=DeploymentStateResponse, summary="Get Blue/Green Deployment State")
def get_deployment_state():
    """
    Returns the live router state, active color, versions, and traffic percentage split.
    """
    driver = get_deployment_driver()
    state = driver.get_state()
    return DeploymentStateResponse(
        active_color=state["active_color"],
        blue_version=state["blue_version"],
        green_version=state["green_version"],
        blue_traffic_percent=state["blue_traffic_percent"],
        green_traffic_percent=state["green_traffic_percent"],
        last_switch_at=state["last_switch_at"],
        notes=state["notes"],
    )


@router.post("/rollback", response_model=DeploymentStateResponse, summary="Manual Administrative Rollback")
def manual_rollback(_: bool = Depends(verify_api_key_optional)):
    """
    Manually reverts traffic to the stable Blue environment.
    """
    driver = get_deployment_driver()
    driver.rollback_to_blue()
    state = driver.get_state()
    return DeploymentStateResponse(
        active_color=state["active_color"],
        blue_version=state["blue_version"],
        green_version=state["green_version"],
        blue_traffic_percent=state["blue_traffic_percent"],
        green_traffic_percent=state["green_traffic_percent"],
        last_switch_at=state["last_switch_at"],
        notes="Manual administrator rollback performed",
    )
