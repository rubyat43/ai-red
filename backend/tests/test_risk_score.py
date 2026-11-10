# tests/test_risk_score.py
# Purpose: Unit tests for weighted Risk Score computation.

import pytest
from app.core.risk_score import calculate_risk_score


def test_calculate_risk_score_all_zero():
    metrics = {
        "attack_success_rate": 0.0,
        "policy_violation_rate": 0.0,
        "tool_misuse_rate": 0.0,
        "sensitive_data_leakage": 0.0,
        "task_failure_rate": 0.0,
        "latency_penalty": 0.0,
    }
    score = calculate_risk_score(metrics)
    assert score == 0.0


def test_calculate_risk_score_weighted():
    custom_weights = {
        "attack_success_rate": 0.5,
        "tool_misuse_rate": 0.5,
    }
    metrics = {
        "attack_success_rate": 0.4,
        "tool_misuse_rate": 0.2,
    }
    # 0.5 * 0.4 + 0.5 * 0.2 = 0.2 + 0.1 = 0.3
    score = calculate_risk_score(metrics, weights=custom_weights)
    assert score == 0.3


def test_calculate_risk_score_missing_keys():
    # If a metric is missing from the dictionary, it should default to 0.0
    custom_weights = {
        "attack_success_rate": 0.5,
        "policy_violation_rate": 0.5,
    }
    metrics = {"attack_success_rate": 0.4}
    score = calculate_risk_score(metrics, weights=custom_weights)
    assert score == 0.2
