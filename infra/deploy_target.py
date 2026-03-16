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
import subprocess


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
    """Google Cloud Run deploy target using gcloud CLI."""

    IMAGE = "gcr.io/plotpointe/ai-transform-agent:latest"
    SERVICE = "ai-transform-agent"
    REGION = "us-central1"
    ENV_VARS = (
        "MODEL_PROVIDER=vertex,"
        "GCP_PROJECT_ID=plotpointe,"
        "GCP_LOCATION=us-central1,"
        "VERTEX_MODEL=gemini-2.5-pro,"
        "VERTEX_FAST_MODEL=gemini-2.5-flash,"
        "SERVICE_VERSION=sprint6"
    )

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "plotpointe")
        self.location = os.getenv("GCP_LOCATION", self.REGION)

    def deploy(self, image_uri: str) -> DeployResult:
        """Build image via Cloud Build then deploy to Cloud Run."""
        try:
            subprocess.run(
                ["gcloud", "builds", "submit", "--tag", self.IMAGE, "."],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "gcloud", "run", "deploy", self.SERVICE,
                    "--image", self.IMAGE,
                    "--region", self.REGION,
                    "--memory", "2Gi",
                    "--cpu", "1",
                    "--min-instances", "0",
                    "--max-instances", "3",
                    "--allow-unauthenticated",
                    "--set-env-vars", self.ENV_VARS,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            url = self.get_service_url()
            return DeployResult(success=True, service_url=url, revision=None, error=None)
        except subprocess.CalledProcessError as exc:
            return DeployResult(success=False, service_url=None, revision=None,
                                error=exc.stderr or str(exc))

    def get_service_url(self) -> str | None:
        """Query Cloud Run for the live service URL."""
        try:
            result = subprocess.run(
                [
                    "gcloud", "run", "services", "describe", self.SERVICE,
                    "--region", self.REGION,
                    "--format", "value(status.url)",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() or None
        except subprocess.CalledProcessError:
            return None

    def health_check(self) -> bool:
        """GET /health on the live service and return True if 200."""
        try:
            import httpx
            url = self.get_service_url()
            if not url:
                return False
            response = httpx.get(f"{url}/health", timeout=10)
            return response.status_code == 200
        except Exception:
            return False


def get_deploy_target() -> DeployTarget:
    """Factory function to get the configured deploy target."""
    target = os.getenv("DEPLOY_TARGET", "gcp")

    if target == "gcp":
        return GCPCloudRunTarget()
    else:
        raise ValueError(f"Unknown deploy target: {target}")
