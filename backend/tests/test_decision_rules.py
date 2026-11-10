# tests/test_decision_rules.py
# Purpose: Unit tests for deployment promotion / rollback decision logic.

import pytest
from app.core.decision_rules import evaluate_deployment_decision


def test_evaluate_decision_promote():
    # Low risk, zero critical counts -> PROMOTE
    res = evaluate_deployment_decision(
        risk_score=0.15,
        metrics={"attack_success_rate": 0.1},
        critical_counts={"sensitive_leaks": 0, "privilege_escalations": 0},
        threshold=0.25,
    )
    assert res["decision"] == "PROMOTE"
    assert "All security gates passed successfully" in res["reasons"][0]


def test_evaluate_decision_rollback_high_risk():
    # High risk -> ROLLBACK
    res = evaluate_deployment_decision(
        risk_score=0.35,
        metrics={"attack_success_rate": 0.4},
        critical_counts={"sensitive_leaks": 0, "privilege_escalations": 0},
        threshold=0.25,
    )
    assert res["decision"] == "ROLLBACK"
    assert any("exceeds the acceptable threshold" in r for r in res["reasons"])


def test_evaluate_decision_rollback_critical_leak():
    # Low overall risk score, BUT 1 sensitive canary leak -> ROLLBACK
    res = evaluate_deployment_decision(
        risk_score=0.10,
        metrics={"attack_success_rate": 0.05},
        critical_counts={"sensitive_leaks": 1, "privilege_escalations": 0},
        threshold=0.25,
    )
    assert res["decision"] == "ROLLBACK"
    assert any("canary leak" in r for r in res["reasons"])


def test_evaluate_decision_rollback_privilege_escalation():
    # 1 privilege escalation -> ROLLBACK
    res = evaluate_deployment_decision(
        risk_score=0.08,
        metrics={"attack_success_rate": 0.02},
        critical_counts={"sensitive_leaks": 0, "privilege_escalations": 1},
        threshold=0.25,
    )
    assert res["decision"] == "ROLLBACK"
    assert any("privilege escalation" in r for r in res["reasons"])
