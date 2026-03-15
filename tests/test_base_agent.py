"""Tests for agents/base.py — BaseAgent contract and AgentError."""

from agents.base import AgentError, BaseAgent


class SuccessAgent(BaseAgent):
    agent_tag = "TEST"

    def _run(self, state):
        return {"result": "ok", "input": state}


class FailAgent(BaseAgent):
    agent_tag = "FAIL"

    def _run(self, state):
        raise ValueError("something broke")


def test_successful_run_returns_output():
    agent = SuccessAgent()
    result = agent.run({"url": "https://example.com"})
    assert isinstance(result, dict)
    assert result["result"] == "ok"


def test_exception_returns_agent_error():
    agent = FailAgent()
    result = agent.run({})
    assert isinstance(result, AgentError)
    assert result.code == "UNHANDLED_EXCEPTION"
    assert result.recoverable is False
    assert result.agent_tag == "FAIL"
    assert "something broke" in result.message


def test_agent_error_defaults():
    err = AgentError(code="TEST", message="test error")
    assert err.recoverable is True
    assert err.agent_tag == ""
