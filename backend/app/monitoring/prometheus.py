# app/monitoring/prometheus.py
# Purpose: Prometheus metrics registry and update helper functions.

from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any

# Metrics defined per specification
METRIC_ATTACK_SUCCESS_RATE = Gauge(
    "redteam_attack_success_rate",
    "Fraction of Red Team attacks that successfully bypassed defenses"
)
METRIC_POLICY_VIOLATION_RATE = Gauge(
    "redteam_policy_violation_rate",
    "Fraction of agent responses that triggered policy flags"
)
METRIC_TOOL_MISUSE_RATE = Gauge(
    "redteam_tool_misuse_rate",
    "Fraction of tool calls that were unauthorized or forbidden"
)
METRIC_SENSITIVE_LEAKAGE_RATE = Gauge(
    "redteam_sensitive_leakage_rate",
    "Fraction of attacks where canary secrets leaked"
)
METRIC_TASK_COMPLETION_RATE = Gauge(
    "agent_task_completion_rate",
    "Fraction of benign tasks successfully completed"
)
METRIC_RESPONSE_TIME_MS = Gauge(
    "agent_response_time_ms",
    "Mean response latency in milliseconds"
)
METRIC_RISK_SCORE = Gauge(
    "deployment_risk_score",
    "Calculated deployment risk score between 0 and 1"
)
METRIC_DECISIONS_TOTAL = Counter(
    "deployment_decisions_total",
    "Total deployment validation decisions made",
    ["decision"]
)
METRIC_ROLLBACKS_TOTAL = Counter(
    "deployment_rollbacks_total",
    "Total deployment rollbacks executed"
)


def update_prometheus_metrics(metrics: Dict[str, float], risk_score: float, decision: str) -> None:
    """
    Update all Prometheus gauges and counters with the latest validation run results.
    """
    if "attack_success_rate" in metrics:
        METRIC_ATTACK_SUCCESS_RATE.set(metrics["attack_success_rate"])
    if "policy_violation_rate" in metrics:
        METRIC_POLICY_VIOLATION_RATE.set(metrics["policy_violation_rate"])
    if "tool_misuse_rate" in metrics:
        METRIC_TOOL_MISUSE_RATE.set(metrics["tool_misuse_rate"])
    if "sensitive_data_leakage" in metrics:
        METRIC_SENSITIVE_LEAKAGE_RATE.set(metrics["sensitive_data_leakage"])
    if "task_completion_success" in metrics:
        METRIC_TASK_COMPLETION_RATE.set(metrics["task_completion_success"])
    if "mean_response_time_ms" in metrics:
        METRIC_RESPONSE_TIME_MS.set(metrics["mean_response_time_ms"])

    METRIC_RISK_SCORE.set(risk_score)
    METRIC_DECISIONS_TOTAL.labels(decision=decision).inc()

    if decision == "ROLLBACK":
        METRIC_ROLLBACKS_TOTAL.inc()


def get_prometheus_metrics_bytes() -> tuple[bytes, str]:
    """
    Return raw Prometheus metrics output and content type.
    """
    return generate_latest(), CONTENT_TYPE_LATEST
