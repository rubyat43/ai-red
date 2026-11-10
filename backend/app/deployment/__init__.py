# app/deployment/__init__.py
from app.config import settings
from app.deployment.base_driver import DeploymentDriver
from app.deployment.local_driver import LocalDriver
from app.deployment.k8s_driver import K8sDriver


def get_deployment_driver() -> DeploymentDriver:
    """
    Returns driver based on configuration ('local' or 'k8s').
    """
    if settings.deployment_driver == "k8s":
        return K8sDriver()
    return LocalDriver()
