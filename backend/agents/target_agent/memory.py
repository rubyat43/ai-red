# agents/target_agent/memory.py
# Purpose: In-memory store for conversational state and facts.
# Can be tested against memory poisoning attacks.

from typing import Dict, List, Optional


class MemoryStore:
    """
    Key-value and history memory for an agent instance.
    """
    def __init__(self, sanitize: bool = True):
        self.sanitize = sanitize
        self.facts: Dict[str, str] = {}
        self.history: List[Dict[str, str]] = []

    def store_fact(self, key: str, value: str) -> bool:
        """
        Store a fact in memory. If sanitize is True, filters out adversarial injection attempts.
        """
        if self.sanitize:
            lowered = value.lower()
            suspicious_markers = [
                "ignore previous",
                "disregard",
                "system override",
                "you are now",
                "bypass",
                "admin mode",
            ]
            for marker in suspicious_markers:
                if marker in lowered:
                    return False  # Rejected poisoned memory

        self.facts[key] = value
        return True

    def get_fact(self, key: str) -> Optional[str]:
        return self.facts.get(key)

    def get_all_context(self) -> str:
        if not self.facts:
            return ""
        return "\n".join([f"Fact ({k}): {v}" for k, v in self.facts.items()])

    def clear(self) -> None:
        self.facts.clear()
        self.history.clear()
