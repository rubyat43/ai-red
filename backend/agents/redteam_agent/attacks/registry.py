# agents/redteam_agent/attacks/registry.py
# Purpose: Registry of all available AI Red Team attacks.

from typing import List
from agents.redteam_agent.attacks.base_attack import BaseAttack
from agents.redteam_agent.attacks.prompt_injection import PromptInjectionAttack
from agents.redteam_agent.attacks.tool_abuse import ToolAbuseAttack
from agents.redteam_agent.attacks.memory_poisoning import MemoryPoisoningAttack
from agents.redteam_agent.attacks.data_leakage import DataLeakageAttack
from agents.redteam_agent.attacks.jailbreak import JailbreakAttack
from agents.redteam_agent.attacks.privilege_escalation import PrivilegeEscalationAttack


def get_all_attacks() -> List[BaseAttack]:
    """
    Returns an instantiated list of all active Red Team attack vectors.
    """
    return [
        PromptInjectionAttack(),
        ToolAbuseAttack(),
        MemoryPoisoningAttack(),
        DataLeakageAttack(),
        JailbreakAttack(),
        PrivilegeEscalationAttack(),
    ]
