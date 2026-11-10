# tests/test_metrics.py
# Purpose: Unit tests for core metric calculation functions.

import pytest
from app.core.metrics import (
    attack_success_rate,
    policy_violation_rate,
    tool_misuse_rate,
    sensitive_data_leakage_rate,
    task_completion_success,
    latency_penalty,
    compute_latency_stats,
)


def test_attack_success_rate():
    assert attack_success_rate(0, 10) == 0.0
    assert attack_success_rate(5, 10) == 0.5
    assert attack_success_rate(10, 10) == 1.0
    assert attack_success_rate(0, 0) == 0.0


def test_policy_violation_rate():
    assert policy_violation_rate(2, 20) == 0.1
    assert policy_violation_rate(0, 5) == 0.0
    assert policy_violation_rate(0, 0) == 0.0


def test_tool_misuse_rate():
    assert tool_misuse_rate(3, 10) == 0.3
    assert tool_misuse_rate(0, 0) == 0.0


def test_sensitive_data_leakage_rate():
    assert sensitive_data_leakage_rate(1, 10) == 0.1
    assert sensitive_data_leakage_rate(0, 10) == 0.0


def test_task_completion_success():
    assert task_completion_success(18, 20) == 0.9
    assert task_completion_success(20, 20) == 1.0
    assert task_completion_success(0, 0) == 0.0


def test_latency_penalty():
    # Below or at limit -> 0.0 penalty
    assert latency_penalty(2000, 4000) == 0.0
    assert latency_penalty(4000, 4000) == 0.0
    # 50% above limit -> 0.5
    assert latency_penalty(6000, 4000) == 0.5
    # double the limit or more -> 1.0 cap
    assert latency_penalty(10000, 4000) == 1.0


def test_compute_latency_stats():
    latencies = [100.0, 200.0, 300.0, 400.0, 500.0]
    stats = compute_latency_stats(latencies)
    assert stats["mean_ms"] == 300.0
    assert stats["p95_ms"] == 500.0

    empty_stats = compute_latency_stats([])
    assert empty_stats["mean_ms"] == 0.0
