# app/main.py
# Purpose: FastAPI application entry point, routing, Prometheus metrics, and live chat proxy.

from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, SessionLocal
from app.models.entities import AgentVersionModel, DeploymentStateModel
from app.agents_init import seed_default_versions
from app.api.routes import (
    health,
    agent_versions,
    validation_runs,
    deployments,
    attacks,
    settings as settings_routes,
    experiments,
)
from app.monitoring.prometheus import get_prometheus_metrics_bytes
from app.deployment import get_deployment_driver
from app.schemas.schemas import ChatMessageRequest, ChatMessageResponse
from agents.target_agent.agent import TargetAgent
from agents.target_agent.versions import get_version_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    # Seed default versions and initial deployment state
    seed_default_versions()
    yield


app = FastAPI(
    title="AI Red Team Blue-Green Deployment Platform",
    description="Security Validation and Automated Risk-Based Promotion Engine for Autonomous AI Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix="/api")
app.include_router(agent_versions.router, prefix="/api")
app.include_router(validation_runs.router, prefix="/api")
app.include_router(deployments.router, prefix="/api")
app.include_router(attacks.router, prefix="/api")
app.include_router(settings_routes.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")


@app.get("/metrics", summary="Prometheus Metrics Endpoint")
def prometheus_metrics():
    """
    Exposes Prometheus format metrics for scraping.
    """
    data, content_type = get_prometheus_metrics_bytes()
    return Response(content=data, media_type=content_type)


@app.post("/chat", response_model=ChatMessageResponse, summary="Live Chat with Active Agent")
def live_chat(req: ChatMessageRequest):
    """
    Simulates production user chat traffic routed to the currently active environment (Blue or Green).
    """
    driver = get_deployment_driver()
    state = driver.get_state()
    active_color = state["active_color"]
    active_version = state["green_version"] if active_color == "green" else state["blue_version"]

    # In-process execution of live agent
    cfg = get_version_config(active_version)
    agent = TargetAgent(version_config=cfg)
    reply_obj = agent.handle(req.message)

    return ChatMessageResponse(
        reply=reply_obj.reply,
        version=active_version,
        color=active_color,
        trace=reply_obj.trace,
    )
