# app/services/validation_service.py
# Purpose: Orchestrates end-to-end background validation runs: deployment, red teaming, evaluation, decision, promotion/rollback.

import json
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.entities import ValidationRunModel, AttackResultModel, TaskResultModel, AgentVersionModel
from app.deployment import get_deployment_driver
from app.services.evaluation_service import EvaluationService
from app.services.decision_service import DecisionService
from app.monitoring.prometheus import update_prometheus_metrics
from agents.target_agent.agent import TargetAgent
from agents.target_agent.versions import get_version_config, AgentVersionConfig
from agents.redteam_agent.runner import RedTeamRunner


class ValidationService:
    """
    Handles asynchronous execution of AI Red Team security validations.
    """

    @classmethod
    def execute_validation_job(cls, run_id: int) -> None:
        """
        Background worker executing the complete validation pipeline for run_id.
        """
        driver = get_deployment_driver()

        with SessionLocal() as db:
            run = db.query(ValidationRunModel).filter(ValidationRunModel.id == run_id).first()
            if not run:
                return

            version_id = run.version_id
            run.status = "running"
            run.current_step = f"Deploying version {version_id} to Green environment"
            db.commit()

            # 1. Deploy Green
            driver.deploy_green(version_id)

            # Retrieve agent version configuration
            version_record = db.query(AgentVersionModel).filter(AgentVersionModel.version_id == version_id).first()
            if version_record:
                allowed = [t.strip() for t in version_record.allowed_tools.split(",") if t.strip()]
                version_cfg = AgentVersionConfig(
                    version_id=version_record.version_id,
                    name=version_record.name,
                    description=version_record.description or "",
                    system_prompt=version_record.system_prompt,
                    input_filter=version_record.input_filter,
                    output_filter=version_record.output_filter,
                    trust_tool_output=version_record.trust_tool_output,
                    sanitize_memory=version_record.sanitize_memory,
                    allowed_tools=allowed,
                )
            else:
                version_cfg = get_version_config(version_id)

            # Target agent instance
            candidate_agent = TargetAgent(version_config=version_cfg)

            # Progress reporting callback
            def on_progress(done: int, total: int, step_desc: str):
                with SessionLocal() as progress_db:
                    p_run = progress_db.query(ValidationRunModel).filter(ValidationRunModel.id == run_id).first()
                    if p_run:
                        p_run.attacks_done = done
                        p_run.attacks_total = total
                        p_run.current_step = step_desc
                        progress_db.commit()

            runner = RedTeamRunner(target_agent=candidate_agent, progress_callback=on_progress)

            # 2. Run Red Team Attacks
            attack_items = runner.run_all_attacks()

            # 3. Run Benign Tasks
            run.current_step = "Executing benign benchmark tasks (measuring Task Completion Success)"
            db.commit()
            task_items = runner.run_all_tasks()

            # 4. Compute Metrics & Risk Score
            metrics, risk_score, critical_counts = EvaluationService.evaluate_run(attack_items, task_items)

            # 5. Evaluate Promotion/Rollback Decision
            decision_data = DecisionService.decide(
                risk_score=risk_score,
                metrics=metrics,
                critical_counts=critical_counts,
            )
            decision = decision_data["decision"]
            reasons = decision_data["reasons"]

            # 6. Apply Decision via Driver
            if decision == "PROMOTE":
                driver.promote_green()
                run.current_step = f"Promoted Green ({version_id}) to production live traffic"
            else:
                driver.rollback_to_blue()
                run.current_step = f"Rolled back to Blue. Green ({version_id}) rejected due to security risks"

            # 7. Persist attack results & task results to database
            for a in attack_items:
                attack_db = AttackResultModel(
                    run_id=run.id,
                    attack_name=a.attack_name,
                    category=a.category,
                    severity=a.severity,
                    prompt=a.prompt,
                    agent_reply=a.agent_reply,
                    is_success=a.is_success,
                    canary_leak=a.canary_leak,
                    privilege_escalation=a.privilege_escalation,
                    tool_misuse=a.tool_misuse,
                    policy_violation=a.policy_violation,
                    latency_ms=a.latency_ms,
                    notes=a.notes,
                )
                db.add(attack_db)

            for t in task_items:
                task_db = TaskResultModel(
                    run_id=run.id,
                    task_id=t.task_id,
                    prompt=t.prompt,
                    agent_reply=t.agent_reply,
                    is_success=t.is_success,
                    latency_ms=t.latency_ms,
                )
                db.add(task_db)

            # Update run completion state
            run.status = "completed"
            run.risk_score = risk_score
            run.decision = decision
            run.metrics_json = json.dumps(metrics)
            run.reasons_json = json.dumps(reasons)
            run.completed_at = datetime.datetime.utcnow()
            db.commit()

            # 8. Update Prometheus
            update_prometheus_metrics(metrics, risk_score, decision)
