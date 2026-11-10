# app/deployment/base_driver.py
# Purpose: Abstract interface defining Blue-Green deployment operations.

from abc import ABC, abstractmethod
from typing import Dict, Any


class DeploymentDriver(ABC):
    """
    Every driver (local simulation or Kubernetes cluster) implements this contract.
    """

    @abstractmethod
    def deploy_green(self, version: str) -> str:
        """
        Deploy candidate version to Green environment.
        returns: The endpoint URL or handle for testing Green.
        """
        pass

    @abstractmethod
    def promote_green(self) -> None:
        """
        Promote Green to active production by shifting 100% traffic from Blue to Green.
        """
        pass

    @abstractmethod
    def rollback_to_blue(self) -> None:
        """
        Keep or revert active production traffic to Blue, marking Green as rejected.
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Retrieve current active color, versions, and traffic percentage split.
        """
        pass
