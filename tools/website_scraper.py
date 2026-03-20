"""WebsiteScraperTool — wraps ScraperAgent with the Tool ABC interface."""

from __future__ import annotations

from agents.base import AgentError
from agents.scraper import ScraperAgent
from orchestrator.tool_registry import Tool


class WebsiteScraperTool(Tool):
    """Tool that delegates to ScraperAgent.

    Accepts input_data with keys:
      - url (str): company URL to scrape
      - dry_run (bool): if True, returns fixture data without HTTP calls
    """

    tool_id = "website_scraper"

    def __init__(self) -> None:
        self._agent = ScraperAgent()

    def run(self, input_data: dict) -> dict | AgentError:
        """Run the scraper. dry_run is read from input_data, not from os.environ."""
        return self._agent.run(input_data)
