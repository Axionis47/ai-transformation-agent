"""Deploy target abstraction layer.

All deploy operations go through this interface.
Never call GCP, Fly.io, or other providers directly.

Usage:
    from infra.deploy_target import get_deploy_target

    target = get_deploy_target()
    target.deploy(image_uri="gcr.io/project/image:tag")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import os


@dataclass
class DeployResult:
    """Result of a deploy operation."""
    success: bool
    service_url: str | None
    revision: str | None
    error: str | None


class DeployTarget(ABC):
    """Abstract base class for deploy targets."""

    @abstractmethod
    def deploy(self, image_uri: str) -> DeployResult:
        """Deploy a container image to the target."""
        pass

    @abstractmethod
    def get_service_url(self) -> str | None:
        """Get the URL of the deployed service."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the deployed service is healthy."""
        pass


class GCPCloudRunTarget(DeployTarget):
    """Google Cloud Run deploy target."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "us-central1")
        self.service_name = "ai-transform-agent"

    def deploy(self, image_uri: str) -> DeployResult:
        # Implementation will use gcloud CLI or Cloud Run Admin API
        raise NotImplementedError("GCP deploy not yet implemented")

    def get_service_url(self) -> str | None:
        # Implementation will query Cloud Run service
        raise NotImplementedError("GCP service URL lookup not yet implemented")

    def health_check(self) -> bool:
        # Implementation will call /health endpoint
        raise NotImplementedError("GCP health check not yet implemented")


def get_deploy_target() -> DeployTarget:
    """Factory function to get the configured deploy target."""
    target = os.getenv("DEPLOY_TARGET", "gcp")

    if target == "gcp":
        return GCPCloudRunTarget()
    else:
        raise ValueError(f"Unknown deploy target: {target}")
