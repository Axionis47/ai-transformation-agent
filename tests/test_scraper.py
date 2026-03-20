"""Unit tests for ScraperAgent — source registry, fault tolerance, and dry-run."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from agents.scraper import ScraperAgent, ScraperConfig, SourceSpec

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_company.json"


class TestScraperFixture:
    """Verify the dry-run fixture has all required fields."""

    def setup_method(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text())

    def test_fixture_has_url(self) -> None:
        assert "url" in self.fixture
        assert self.fixture["url"].startswith("http")

    def test_fixture_has_about_text(self) -> None:
        assert "about_text" in self.fixture
        assert len(self.fixture["about_text"]) > 50

    def test_fixture_has_product_text(self) -> None:
        assert "product_text" in self.fixture
        assert len(self.fixture["product_text"]) > 20

    def test_fixture_has_blog_text(self) -> None:
        assert "blog_text" in self.fixture
        assert len(self.fixture["blog_text"]) > 20

    def test_fixture_has_team_text(self) -> None:
        assert "team_text" in self.fixture
        assert len(self.fixture["team_text"]) > 20

    def test_fixture_has_job_postings(self) -> None:
        assert "job_postings" in self.fixture
        assert isinstance(self.fixture["job_postings"], list)
        assert len(self.fixture["job_postings"]) >= 3

    def test_fixture_job_postings_are_rich(self) -> None:
        for posting in self.fixture["job_postings"]:
            assert len(posting) >= 100, f"Posting too short: {posting[:40]}"

    def test_fixture_has_pages_fetched(self) -> None:
        pages = self.fixture["pages_fetched"]
        assert isinstance(pages, list)
        assert len(pages) >= 1

    def test_fixture_has_fetch_summary(self) -> None:
        fs = self.fixture["fetch_summary"]
        assert "attempted" in fs
        assert "succeeded" in fs
        assert "failed" in fs


class TestScraperDryRun:
    """ScraperAgent dry-run mode returns fixture data."""

    def test_dry_run_returns_dict(self) -> None:
        with patch.dict(os.environ, {"DRY_RUN": "true"}):
            agent = ScraperAgent()
            result = agent.run({"url": "https://example.com"})
        assert isinstance(result, dict)

    def test_dry_run_returns_url(self) -> None:
        with patch.dict(os.environ, {"DRY_RUN": "true"}):
            agent = ScraperAgent()
            result = agent.run({"url": "https://example.com"})
        assert "url" in result

    def test_dry_run_returns_product_text(self) -> None:
        with patch.dict(os.environ, {"DRY_RUN": "true"}):
            agent = ScraperAgent()
            result = agent.run({"url": "https://example.com"})
        assert "product_text" in result and result["product_text"]

    def test_dry_run_returns_pages_fetched(self) -> None:
        with patch.dict(os.environ, {"DRY_RUN": "true"}):
            agent = ScraperAgent()
            result = agent.run({"url": "https://example.com"})
        assert isinstance(result["pages_fetched"], list)


class TestParseJobPostings:
    """_parse_job_postings splits multi-posting pages correctly."""

    def setup_method(self) -> None:
        self.agent = ScraperAgent()
        self.config = ScraperConfig()

    def test_empty_string_returns_empty_list(self) -> None:
        assert self.agent._parse_job_postings("", self.config) == []

    def test_whitespace_only_returns_empty_list(self) -> None:
        assert self.agent._parse_job_postings("   \n\n  ", self.config) == []

    def test_multi_posting_splits_on_separator(self) -> None:
        text = "Senior Engineer\n\nBuild APIs.\n\n---\nProduct Manager\n\nOwn roadmap."
        result = self.agent._parse_job_postings(text, self.config)
        assert len(result) >= 2

    def test_single_posting_returns_one_item(self) -> None:
        text = "One job posting with no structural separators at all in it."
        result = self.agent._parse_job_postings(text, self.config)
        assert len(result) == 1

    def test_respects_max_job_postings(self) -> None:
        config = ScraperConfig(max_job_postings=2)
        parts = [f"Job {i}\n\nDescription for job number {i}." for i in range(6)]
        text = "\n\n".join(parts)
        result = self.agent._parse_job_postings(text, config)
        assert len(result) <= 2

    def test_respects_max_chars_per_posting(self) -> None:
        config = ScraperConfig(max_chars_per_posting=50)
        text = "A" * 200
        result = self.agent._parse_job_postings(text, config)
        for chunk in result:
            assert len(chunk) <= 50

    def test_double_newline_cap_split(self) -> None:
        text = "Data Engineer\n\nBuild pipelines.\n\nML Engineer\n\nTrain models."
        result = self.agent._parse_job_postings(text, self.config)
        assert len(result) >= 2


class TestSourceRegistryLive:
    """Source registry iterates all sources with per-source fault tolerance."""

    def _make_response(self, status: int, text: str = "<html><body>content</body></html>") -> MagicMock:
        m = MagicMock()
        m.status_code = status
        m.text = text
        return m

    def test_all_sources_attempted(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = self._make_response(200)
        config = ScraperConfig()

        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com", "config": config})

        assert result["fetch_summary"]["attempted"] == len(config.sources)

    def test_one_source_failure_does_not_break_others(self) -> None:
        mock_client = MagicMock()

        def side_effect(url: str):
            if "/careers" in url or "/jobs" in url or "/join-us" in url:
                return self._make_response(404)
            return self._make_response(200, "<html><body>page content here</body></html>")

        mock_client.get.side_effect = side_effect

        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com"})

        assert isinstance(result, dict)
        assert result["fetch_summary"]["succeeded"] >= 1
        assert "careers" in result["fetch_summary"]["failed"]

    def test_all_404_returns_empty_pages_fetched(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = self._make_response(404)

        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com"})

        assert result.get("pages_fetched") == []
        assert result["fetch_summary"]["succeeded"] == 0

    def test_result_includes_blog_and_team_fields(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = self._make_response(200)

        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com"})

        assert "blog_text" in result
        assert "team_text" in result

    def test_custom_config_max_job_postings(self) -> None:
        mock_client = MagicMock()
        careers_html = "<html><body>" + "\n\n".join(
            [f"Job Title {i}\n\nResponsibilities and requirements for role {i}." for i in range(8)]
        ) + "</body></html>"

        def side_effect(url: str):
            if any(p in url for p in ["/careers", "/jobs", "/join-us"]):
                return self._make_response(200, careers_html)
            return self._make_response(404)

        mock_client.get.side_effect = side_effect

        config = ScraperConfig(max_job_postings=3)
        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com", "config": config})

        assert len(result.get("job_postings", [])) <= 3
