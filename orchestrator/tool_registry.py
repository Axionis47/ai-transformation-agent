"""Tool registry — abstract Tool contract and ToolRegistry singleton."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents.base import AgentError


class Tool(ABC):
    """Abstract base class for pipeline tools.

    Each tool wraps an agent and exposes a uniform run() interface.
    Subclasses must set `tool_id` as a class attribute.
    """

    tool_id: str  # Must be overridden by each subclass

    @abstractmethod
    def run(self, input_data: dict) -> dict | AgentError:
        """Execute the tool with given input.

        Returns a result dict on success, or AgentError on failure.
        Never raises — errors are returned, not thrown.
        """
        ...


class ToolRegistry:
    """Registry for pipeline tools.

    Tools register themselves by tool_id. Pipeline stages retrieve
    tools by ID, decoupling stage logic from concrete agent classes.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Add a tool to the registry keyed by its tool_id."""
        self._tools[tool.tool_id] = tool

    def get(self, tool_id: str) -> Tool:
        """Retrieve a registered tool by ID.

        Raises KeyError if the tool_id is not registered.
        """
        if tool_id not in self._tools:
            raise KeyError(f"Tool '{tool_id}' not registered")
        return self._tools[tool_id]

    def list_ids(self) -> list[str]:
        """Return all registered tool IDs."""
        return list(self._tools.keys())


# Singleton — import this in pipeline and tool modules
registry = ToolRegistry()

# Register built-in tools after defining the singleton
from tools.website_scraper import WebsiteScraperTool  # noqa: E402

registry.register(WebsiteScraperTool())
