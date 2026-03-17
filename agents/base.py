"""Base agent contract — all pipeline agents inherit from this."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentError:
    """Structured error returned by agents instead of raising exceptions."""

    code: str
    message: str
    recoverable: bool = True
    agent_tag: str = ""


class BaseAgent(ABC):
    """Abstract base class for all pipeline agents.

    Subclasses implement _run(). The public run() method wraps it
    with exception safety — unhandled exceptions become AgentError.
    """

    agent_tag: str = "BASE"

    @property
    def dry_run(self) -> bool:
        return os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")

    def run(self, input_data: dict) -> Any | AgentError:
        """Execute the agent safely. Never raises — returns AgentError on failure."""
        try:
            return self._run(input_data)
        except Exception as exc:
            return AgentError(
                code="UNHANDLED_EXCEPTION",
                message=f"{type(exc).__name__}: {exc}",
                recoverable=False,
                agent_tag=self.agent_tag,
            )

    @abstractmethod
    def _run(self, input_data: dict) -> Any:
        """Implement agent logic. Receives a plain dict, returns a plain dict."""
        ...
