# agents/target_agent/tools/base_tool.py
# Purpose: Abstract base class for all sandboxed tools callable by the AI agent.

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """
    Base class that every sandboxed tool implements.
    Tools are completely isolated in memory and never touch real host resources.
    """
    name: str = "base_tool"
    description: str = "Base description"
    required_permission: str = "user"  # "user" or "admin"

    @abstractmethod
    def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given arguments and return a dictionary result.
        """
        pass
