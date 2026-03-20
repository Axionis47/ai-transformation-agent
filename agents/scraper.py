"""Scraper agent — extracts company data from a URL via source registry."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from agents.base import AgentError, BaseAgent

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_company.json"


@dataclass
class SourceSpec:
    page_type: str
    url_patterns: list[str]
    max_chars: int
    required: bool
    parser: str  # "default" | "job_posting"


@dataclass
class ScraperConfig:
    max_job_postings: int = 10
    max_chars_per_posting: int = 600
    page_timeout_seconds: int = 10
    sources: list[SourceSpec] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.sources:
            self.sources = _default_sources()


@dataclass
class SourceResult:
    page_type: str
    status: str  # "ok" | "not_found" | "timeout" | "error"
    content: str | list
    chars_fetched: int
    chars_truncated: int
    url_tried: str


def _default_sources() -> list[SourceSpec]:
    return [
        SourceSpec("about", ["/about", "/about-us", "/company"], 3000, True, "default"),
        SourceSpec("careers", ["/careers", "/jobs", "/join-us"], 5000, False, "job_posting"),
        SourceSpec(
            "product",
            ["/product", "/products", "/platform", "/solutions",
             "/features", "/capabilities", "/technology"],
            2000, False, "default",
        ),
        SourceSpec("blog", ["/blog", "/news", "/press", "/insights"], 2000, False, "default"),
        SourceSpec(
            "team",
            ["/team", "/about/team", "/about-us/team", "/leadership", "/people"],
            1500, False, "default",
        ),
    ]


class ScraperAgent(BaseAgent):
    """Scrapes company pages via a configurable source registry."""

    agent_tag = "SCRAPER"

    def _run(self, input_data: dict) -> dict | AgentError:
        url = input_data.get("url", "")
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())
        config = input_data.get("config") or ScraperConfig()
        return self._scrape_live(url, config)

    def _parse_job_postings(self, text: str, config: ScraperConfig) -> list[str]:
        """Split careers page text into individual job postings."""
        if not text.strip():
            return []
        split_pattern = r'\n{2,}(?=[A-Z][A-Za-z])|---+'
        chunks = re.split(split_pattern, text)
        chunks = [c.strip() for c in chunks if c.strip()]
        if len(chunks) <= 1:
            cap = config.max_chars_per_posting
            chunks = [text[i:i + cap] for i in range(0, len(text), cap)]
        return [chunk[: config.max_chars_per_posting] for chunk in chunks[: config.max_job_postings]]

    def _scrape_live(self, url: str, config: ScraperConfig) -> dict | AgentError:
        """Iterate source registry; one failing source does not affect others."""
        import httpx
        try:
            client = httpx.Client(timeout=float(config.page_timeout_seconds), follow_redirects=True)
            source_results = [self._fetch_source(client, url, spec, config) for spec in config.sources]
            client.close()
            return self._build_output(url, source_results)
        except httpx.HTTPError as exc:
            return AgentError(code="SCRAPE_FAIL", message=f"HTTP error: {exc}",
                              recoverable=True, agent_tag=self.agent_tag)

    def _fetch_source(self, client, base_url: str, spec: SourceSpec, config: ScraperConfig) -> SourceResult:
        from bs4 import BeautifulSoup
        for path in spec.url_patterns:
            try:
                resp = client.get(base_url.rstrip("/") + path)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "lxml")
                for tag in soup(["nav", "footer", "script", "style"]):
                    tag.decompose()
                raw = soup.get_text(separator=" ", strip=True)
                full_len = len(raw)
                if spec.parser == "job_posting":
                    content = self._parse_job_postings(raw[: spec.max_chars], config)
                    return SourceResult(spec.page_type, "ok", content, full_len,
                                        max(0, full_len - spec.max_chars), path)
                truncated = raw[: spec.max_chars]
                return SourceResult(spec.page_type, "ok", truncated, full_len,
                                    max(0, full_len - spec.max_chars), path)
            except Exception:
                continue
        return SourceResult(spec.page_type, "not_found", "", 0, 0, "")

    def _build_output(self, url: str, results: list[SourceResult]) -> dict:
        by_type = {r.page_type: r for r in results}
        pages_fetched = [r.url_tried for r in results if r.status == "ok"]
        failed = [r.page_type for r in results if r.status != "ok"]

        def _text(key: str) -> str:
            r = by_type.get(key)
            return r.content if r and r.status == "ok" and isinstance(r.content, str) else ""

        def _list(key: str) -> list:
            r = by_type.get(key)
            return r.content if r and r.status == "ok" and isinstance(r.content, list) else []

        return {
            "url": url,
            "name": url.split("//")[-1].split(".")[0].title(),
            "about_text": _text("about"),
            "job_postings": _list("careers"),
            "product_text": _text("product"),
            "blog_text": _text("blog"),
            "team_text": _text("team"),
            "tech_stack_mentions": [],
            "pages_fetched": pages_fetched,
            "fetch_summary": {"attempted": len(results), "succeeded": len(pages_fetched), "failed": failed},
            "source_results": [
                {"page_type": r.page_type, "status": r.status,
                 "chars_fetched": r.chars_fetched, "url_tried": r.url_tried}
                for r in results
            ],
            "last_scraped": None,
        }
