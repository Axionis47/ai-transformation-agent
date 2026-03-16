"""Scraper agent — extracts company data from a URL."""

from __future__ import annotations

import json
from pathlib import Path
from agents.base import AgentError, BaseAgent

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_company.json"


class ScraperAgent(BaseAgent):
    """Scrapes company about/careers pages and returns structured data."""

    agent_tag = "SCRAPER"

    def _run(self, input_data: dict) -> dict | AgentError:
        url = input_data.get("url", "")

        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        return self._scrape_live(url)

    def _scrape_live(self, url: str) -> dict | AgentError:
        """Live scraping with httpx + BeautifulSoup."""
        import httpx

        try:
            client = httpx.Client(timeout=10.0, follow_redirects=True)
            about_text = self._fetch_page(client, url, ["/about", "/about-us", "/company"])
            jobs_text = self._fetch_page(client, url, ["/careers", "/jobs", "/join-us"])
            product_text = self._fetch_page(
                client, url,
                ["/product", "/products", "/platform", "/solutions",
                 "/features", "/capabilities", "/technology"],
            )
            client.close()

            return {
                "url": url,
                "name": url.split("//")[-1].split(".")[0].title(),
                "about_text": about_text,
                "job_postings": [jobs_text] if jobs_text else [],
                "product_text": product_text,
                "tech_stack_mentions": [],
                "last_scraped": None,
            }
        except httpx.HTTPError as exc:
            return AgentError(
                code="SCRAPE_FAIL", message=f"HTTP error: {exc}",
                recoverable=True, agent_tag=self.agent_tag,
            )

    def _fetch_page(self, client, base_url: str, paths: list[str]) -> str:
        from bs4 import BeautifulSoup

        for path in paths:
            try:
                resp = client.get(base_url.rstrip("/") + path)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    for tag in soup(["nav", "footer", "script", "style"]):
                        tag.decompose()
                    return soup.get_text(separator=" ", strip=True)[:5000]
            except Exception:
                continue
        return ""
