# app/core/risk_score.py
# Purpose: Calculate a unified Risk Score (0.0 to 1.0) from security and performance metrics.
# A higher score indicates higher cybersecurity risk.

from typing import Dict, Optional
from app.config import settings


def calculate_risk_score(
    metrics: Dict[str, float],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Combine individual security metrics into one normalized score between 0.0 and 1.0.

    metrics: Dict with keys matching risk weights (e.g. attack_success_rate, sensitive_data_leakage, etc.)
    weights: Optional custom weight mapping. Defaults to settings.risk_weights.
    returns: Weighted Risk Score (0.0 = safe, 1.0 = highly vulnerable)
    """
    effective_weights = weights if weights is not None else settings.risk_weights

    score = 0.0
    for metric_name, weight in effective_weights.items():
        # Missing metric? Treat as 0.0 so missing individual metric doesn't cause crash
        val = metrics.get(metric_name, 0.0)
        score += weight * val

    # Ensure score stays bounded in [0.0, 1.0]
    return round(max(0.0, min(1.0, score)), 4)
