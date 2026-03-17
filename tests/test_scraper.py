"""Unit tests for ScraperAgent — dry-run fixture fields and live scraper structure."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch


from agents.scraper import ScraperAgent

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

    def test_fixture_has_job_postings(self) -> None:
        assert "job_postings" in self.fixture
        assert isinstance(self.fixture["job_postings"], list)
        assert len(self.fixture["job_postings"]) > 0

    def test_fixture_has_pages_fetched(self) -> None:
        assert "pages_fetched" in self.fixture
        pages = self.fixture["pages_fetched"]
        assert isinstance(pages, list)
        assert len(pages) >= 1
        for p in pages:
            assert p.startswith("/"), f"Expected path starting with '/', got: {p}"

    def test_fixture_has_signal_count(self) -> None:
        assert "signal_count" in self.fixture
        assert isinstance(self.fixture["signal_count"], int)
        assert self.fixture["signal_count"] > 0

    def test_fixture_has_tech_stack_mentions(self) -> None:
        assert "tech_stack_mentions" in self.fixture
        assert isinstance(self.fixture["tech_stack_mentions"], list)


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
        assert "product_text" in result
        assert result["product_text"]

    def test_dry_run_returns_pages_fetched(self) -> None:
        with patch.dict(os.environ, {"DRY_RUN": "true"}):
            agent = ScraperAgent()
            result = agent.run({"url": "https://example.com"})
        assert "pages_fetched" in result
        assert isinstance(result["pages_fetched"], list)


class TestScraperLiveStructure:
    """Live scraper returns correct structure including pages_fetched."""

    def _make_mock_response(self, status: int = 200, text: str = "<html><body>content</body></html>") -> MagicMock:
        mock = MagicMock()
        mock.status_code = status
        mock.text = text
        return mock

    def test_live_scrape_returns_pages_fetched(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = self._make_mock_response(200, "<html><body>test page content</body></html>")

        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com"})

        assert isinstance(result, dict)
        assert "pages_fetched" in result
        assert isinstance(result["pages_fetched"], list)

    def test_live_scrape_404_excluded_from_pages_fetched(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = self._make_mock_response(404, "")

        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com"})

        assert isinstance(result, dict)
        assert result.get("pages_fetched") == []

    def test_live_scrape_returns_product_text_field(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = self._make_mock_response(200, "<html><body>product info</body></html>")

        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with patch("httpx.Client", return_value=mock_client):
                agent = ScraperAgent()
                result = agent.run({"url": "https://example.com"})

        assert isinstance(result, dict)
        assert "product_text" in result
