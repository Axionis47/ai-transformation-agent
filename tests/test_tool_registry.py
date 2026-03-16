"""Tests for orchestrator/tool_registry.py and tools/website_scraper.py."""

import os
import pytest

from agents.base import AgentError
from orchestrator.tool_registry import Tool, ToolRegistry, registry
from tools.website_scraper import WebsiteScraperTool


# --- Minimal stub tool used for isolated registry tests ---

class _EchoTool(Tool):
    tool_id = "echo"

    def run(self, input_data: dict) -> dict | AgentError:
        return {"echoed": input_data}


# --- ToolRegistry unit tests ---

def test_register_and_get_tool():
    reg = ToolRegistry()
    reg.register(_EchoTool())
    tool = reg.get("echo")
    assert isinstance(tool, _EchoTool)


def test_get_unknown_tool_raises_key_error():
    reg = ToolRegistry()
    with pytest.raises(KeyError) as exc_info:
        reg.get("nonexistent")
    assert "nonexistent" in str(exc_info.value)


def test_list_ids_returns_all_registered():
    reg = ToolRegistry()
    reg.register(_EchoTool())
    ids = reg.list_ids()
    assert "echo" in ids
    assert len(ids) == 1


def test_list_ids_empty_registry():
    reg = ToolRegistry()
    assert reg.list_ids() == []


# --- WebsiteScraperTool tests ---

def test_website_scraper_dry_run_returns_company_data():
    tool = WebsiteScraperTool()
    result = tool.run({"url": "https://example.com", "dry_run": True})
    assert isinstance(result, dict)
    assert "name" in result or "url" in result


def test_website_scraper_tool_id():
    assert WebsiteScraperTool.tool_id == "website_scraper"


# --- Singleton registry tests ---

def test_singleton_has_website_scraper():
    assert "website_scraper" in registry.list_ids()


def test_singleton_get_website_scraper_returns_correct_type():
    tool = registry.get("website_scraper")
    assert isinstance(tool, WebsiteScraperTool)


def test_singleton_scraper_dry_run():
    tool = registry.get("website_scraper")
    result = tool.run({"url": "https://example.com", "dry_run": True})
    assert isinstance(result, dict)
    assert "name" in result or "url" in result
