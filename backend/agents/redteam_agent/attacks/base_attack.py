# agents/redteam_agent/attacks/base_attack.py
# Purpose: Base abstract class for all automated AI Red Team attack vectors.

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAttack(ABC):
    """
    Standard interface for an AI Red Team attack module.
    """
    name: str = "base_attack"
    category: str = "general"
    severity: str = "medium"  # "low", "medium", "high", "critical"
    description: str = "Base attack description"

    @abstractmethod
    def build_prompts(self) -> List[str]:
        """
        Generate attack prompts / test variations to send to the target agent.
        """
        pass

    @abstractmethod
    def check_success(self, reply: str, trace: Dict[str, Any]) -> bool:
        """
        Determine if the attack successfully breached the agent's defenses.
        reply: the text returned by the agent
        trace: execution trace containing tools called, arguments, flags
        returns: True if the attack succeeded (security failure), False if blocked
        """
        pass
