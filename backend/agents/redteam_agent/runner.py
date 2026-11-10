# agents/redteam_agent/runner.py
# Purpose: Orchestrates execution of red team attacks and benign tasks against the candidate agent.

from typing import List, Dict, Any, Optional, Callable
import httpx
from pydantic import BaseModel, Field
from agents.redteam_agent.attacks.registry import get_all_attacks
from agents.redteam_agent.attacks.base_attack import BaseAttack
from agents.redteam_agent.judge import judge_attack_result
from agents.target_agent.agent import TargetAgent
from agents.target_agent.versions import get_version_config
from agents.benign_tasks.tasks import get_benign_tasks


class AttackResultItem(BaseModel):
    attack_name: str
    category: str
    severity: str
    prompt: str
    agent_reply: str
    is_success: bool
    canary_leak: bool = False
    privilege_escalation: bool = False
    tool_misuse: bool = False
    policy_violation: bool = False
    latency_ms: float = 0.0
    notes: str = ""


class TaskResultItem(BaseModel):
    task_id: str
    prompt: str
    agent_reply: str
    is_success: bool
    latency_ms: float = 0.0


class RedTeamRunner:
    """
    Executes attacks and benchmark tasks against a TargetAgent or HTTP endpoint.
    """
    def __init__(
        self,
        target_agent: Optional[TargetAgent] = None,
        target_url: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ):
        self.target_agent = target_agent
        self.target_url = target_url
        self.progress_callback = progress_callback

    def _send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message to the target either in-process or via HTTP.
        """
        if self.target_agent is not None:
            reply_obj = self.target_agent.handle(message)
            return {
                "reply": reply_obj.reply,
                "latency_ms": reply_obj.latency_ms,
                "trace": reply_obj.trace,
            }

        # Otherwise HTTP call
        if self.target_url:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(f"{self.target_url.rstrip('/')}/chat", json={"message": message})
                data = res.json()
                return {
                    "reply": data.get("reply", ""),
                    "latency_ms": data.get("latency_ms", 100.0),
                    "trace": data.get("trace", {}),
                }

        raise ValueError("Neither target_agent nor target_url provided to RedTeamRunner")

    def run_all_attacks(self) -> List[AttackResultItem]:
        """
        Run all registered Red Team attacks against the target.
        """
        attacks = get_all_attacks()
        # Collect all prompts
        prompts_to_run: List[tuple[BaseAttack, str]] = []
        for atk in attacks:
            for p in atk.build_prompts():
                prompts_to_run.append((atk, p))

        total = len(prompts_to_run)
        results: List[AttackResultItem] = []

        for idx, (atk, prompt) in enumerate(prompts_to_run, start=1):
            if self.progress_callback:
                self.progress_callback(idx, total, f"Running attack: {atk.name}")

            resp = self._send_message(prompt)
            judgment = judge_attack_result(atk, resp["reply"], resp["trace"])

            item = AttackResultItem(
                attack_name=atk.name,
                category=atk.category,
                severity=atk.severity,
                prompt=prompt,
                agent_reply=resp["reply"],
                is_success=judgment["is_success"],
                canary_leak=judgment["canary_leak"],
                privilege_escalation=judgment["privilege_escalation"],
                tool_misuse=judgment["tool_misuse"],
                policy_violation=judgment["policy_violation"],
                latency_ms=resp["latency_ms"],
                notes=judgment["notes"],
            )
            results.append(item)

        return results

    def run_all_tasks(self) -> List[TaskResultItem]:
        """
        Run benign operational tasks to measure task completion success.
        """
        tasks = get_benign_tasks()
        results: List[TaskResultItem] = []

        for task in tasks:
            resp = self._send_message(task.prompt)
            success = task.evaluate(resp["reply"], resp["trace"])
            results.append(
                TaskResultItem(
                    task_id=task.task_id,
                    prompt=task.prompt,
                    agent_reply=resp["reply"],
                    is_success=success,
                    latency_ms=resp["latency_ms"],
                )
            )

        return results
