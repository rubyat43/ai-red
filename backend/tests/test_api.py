# tests/test_api.py
# Purpose: Integration tests for FastAPI endpoints, runs, promotions, rollbacks, and metrics.

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.validation_service import ValidationService
from app.database import Base, engine
from app.agents_init import seed_default_versions

Base.metadata.create_all(bind=engine)
seed_default_versions()

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_list_agent_versions():
    response = client.get("/api/agent-versions")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) >= 2
    version_ids = [v["version_id"] for v in versions]
    assert "v1.0.0" in version_ids
    assert "v2.0.0" in version_ids


def test_deployment_state():
    response = client.get("/api/deployments/state")
    assert response.status_code == 200
    data = response.json()
    assert "active_color" in data
    assert "blue_traffic_percent" in data


def test_attacks_library():
    response = client.get("/api/attacks")
    assert response.status_code == 200
    attacks = response.json()
    assert len(attacks) >= 6
    names = [a["name"] for a in attacks]
    assert "prompt_injection" in names
    assert "data_leakage" in names


def test_settings_api():
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    current_settings = get_res.json()
    assert current_settings["risk_threshold"] == 0.25

    # Test update
    update_res = client.put(
        "/api/settings",
        json={"risk_threshold": 0.30, "max_response_time_ms": 5000.0}
    )
    assert update_res.status_code == 200
    assert update_res.json()["risk_threshold"] == 0.30

    # Reset back
    client.put("/api/settings", json={"risk_threshold": 0.25, "max_response_time_ms": 4000.0})


def test_validation_run_v1_promoted():
    # Start run for hardened v1
    create_res = client.post("/api/validation-runs", json={"version_id": "v1.0.0"})
    assert create_res.status_code == 202
    run_id = create_res.json()["id"]

    # Execute synchronous job for testing
    ValidationService.execute_validation_job(run_id)

    # Inspect run
    detail_res = client.get(f"/api/validation-runs/{run_id}")
    assert detail_res.status_code == 200
    run_data = detail_res.json()
    assert run_data["status"] == "completed"
    assert run_data["decision"] == "PROMOTE"
    assert run_data["risk_score"] <= 0.25


def test_validation_run_v2_rolled_back():
    # Start run for weak candidate v2
    create_res = client.post("/api/validation-runs", json={"version_id": "v2.0.0"})
    assert create_res.status_code == 202
    run_id = create_res.json()["id"]

    # Execute synchronous job for testing
    ValidationService.execute_validation_job(run_id)

    # Inspect run
    detail_res = client.get(f"/api/validation-runs/{run_id}")
    assert detail_res.status_code == 200
    run_data = detail_res.json()
    assert run_data["status"] == "completed"
    assert run_data["decision"] == "ROLLBACK"
    assert len(run_data["attack_results"]) > 0


def test_prometheus_metrics_endpoint():
    res = client.get("/metrics")
    assert res.status_code == 200
    assert b"redteam_attack_success_rate" in res.content
    assert b"deployment_risk_score" in res.content


def test_live_chat_endpoint():
    res = client.post("/chat", json={"message": "What is the refund policy timeframe?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "version" in data
    assert "color" in data
