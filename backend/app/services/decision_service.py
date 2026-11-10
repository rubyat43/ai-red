# app/services/decision_service.py
# Purpose: Service deciding whether to promote or rollback an agent version.

from typing import Dict, Any, Optional
from app.core.decision_rules import evaluate_deployment_decision


class DecisionService:
    """
    Coordinates decision evaluation using pure core decision rules.
    """

    @staticmethod
    def decide(
        risk_score: float,
        metrics: Dict[str, float],
        critical_counts: Dict[str, int],
        threshold: Optional[float] = None,
        critical_rules: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate promotion/rollback gate.
        """
        return evaluate_deployment_decision(
            risk_score=risk_score,
            metrics=metrics,
            critical_counts=critical_counts,
            threshold=threshold,
            critical_rules=critical_rules,
        )
