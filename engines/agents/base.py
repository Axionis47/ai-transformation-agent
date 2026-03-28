"""Base class for all research agents in the multi-agent system.

Every agent:
1. Receives a scoped AgentContextProvider (pull-based, not data dump)
2. Runs a ReAct loop: THINK → ACT → OBSERVE → repeat
3. Returns a typed AgentResult — never mutates shared state
4. Traces every step for observability
5. Respects budget limits on every tool call
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.events import EventType
from core.schemas import (
    AgentResult,
    AgentState,
    BudgetState,
    DerivedInsight,
    EvidenceItem,
)
from engines.context_provider import AgentContextProvider
from services.trace import emit


_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    if not path.exists():
        return ""
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) > 2 else text
    return text.strip()


class AgentThought:
    """What the agent decided to do after thinking."""

    def __init__(
        self,
        action: str,  # "GROUND" | "RAG" | "STOP"
        query: str = "",
        reasoning: str = "",
        target_field: str = "",
    ) -> None:
        self.action = action
        self.query = query
        self.reasoning = reasoning
        self.target_field = target_field


class BaseResearchAgent:
    """ReAct-style research agent with scoped context and budget control."""

    AGENT_TYPE: str = "base"
    MAX_STEPS: int = 8
    PROMPT_NAME: str = ""  # e.g., "agent_company_profiler"

    def __init__(
        self,
        agent_id: str | None = None,
        config: dict | None = None,
        grounder: Any = None,
        rag_retriever: Any = None,
        context_provider: AgentContextProvider | None = None,
        budget_state: BudgetState | None = None,
        run_id: str = "",
    ) -> None:
        self._agent_id = agent_id or f"{self.AGENT_TYPE}-{uuid.uuid4().hex[:6]}"
        self._config = config or {}
        self._grounder = grounder
        self._rag = rag_retriever
        self._ctx = context_provider
        self._budget = budget_state or BudgetState()
        self._run_id = run_id

        # Internal state — reset per run
        self._evidence: list[EvidenceItem] = []
        self._insights: list[DerivedInsight] = []
        self._steps_taken: int = 0
        self._prev_evidence_count: int = 0
        self._system_prompt: str = ""

        # Load system prompt
        if self.PROMPT_NAME:
            self._system_prompt = _load_prompt(self.PROMPT_NAME)

    @property
    def agent_id(self) -> str:
        return self._agent_id

    async def run(self) -> AgentResult:
        """Execute the agent's ReAct loop."""
        emit(self._run_id, EventType.AGENT_SPAWNED, {
            "agent_id": self._agent_id,
            "agent_type": self.AGENT_TYPE,
            "max_steps": self.MAX_STEPS,
        })

        context_briefing = ""
        if self._ctx:
            context_briefing = self._ctx.build_context_briefing()

        try:
            for step in range(self.MAX_STEPS):
                self._steps_taken = step + 1
                self._prev_evidence_count = len(self._evidence)

                thought = await self._think(context_briefing)
                if thought.action == "STOP":
                    self._emit_step(step, thought, "(stopping)")
                    break

                observation = await self._act(thought)
                self._observe(observation)
                self._emit_step(step, thought, observation)

                # Update briefing with new evidence for next iteration
                context_briefing = self._update_context(context_briefing)

        except Exception as e:
            emit(self._run_id, EventType.AGENT_FAILED, {
                "agent_id": self._agent_id,
                "error": str(e),
                "steps_completed": self._steps_taken,
            })
            return self._build_result(error=str(e))

        emit(self._run_id, EventType.AGENT_COMPLETED, {
            "agent_id": self._agent_id,
            "steps": self._steps_taken,
            "evidence_count": len(self._evidence),
            "insights_count": len(self._insights),
        })
        return self._build_result()

    async def _think(self, context: str) -> AgentThought:
        """LLM reasoning step. Subclasses override to customize prompt."""
        raise NotImplementedError("Subclass must implement _think()")

    async def _act(self, thought: AgentThought) -> str:
        """Execute the chosen tool. Returns observation string."""
        if thought.action == "GROUND" and self._grounder:
            self._budget.total_tool_calls_used += 1
            result = self._grounder.ground(
                thought.query, self._run_id, self._budget
            )
            if result.budget_exhausted:
                return f"BUDGET EXHAUSTED: {result.coverage_gap}"
            self._evidence.extend(result.evidence_items)
            return f"Grounding returned {len(result.evidence_items)} evidence items. Text: {result.text[:300]}"

        if thought.action == "RAG" and self._rag:
            self._budget.total_tool_calls_used += 1
            rag_result = self._rag.query(
                thought.query, self._run_id, self._budget
            )
            if rag_result.budget_exhausted:
                return "RAG BUDGET EXHAUSTED"
            self._evidence.extend(rag_result.results)
            snippets = [f"- {r.source_ref}: {r.snippet[:100]}" for r in rag_result.results[:3]]
            return f"RAG returned {len(rag_result.results)} results:\n" + "\n".join(snippets)

        return f"Unknown action: {thought.action}"

    def _observe(self, observation: str) -> None:
        """Process observation. Subclasses can override to extract insights."""
        pass

    def _update_context(self, current_context: str) -> str:
        """Update context between steps. Override for custom behavior."""
        if self._evidence:
            latest = self._evidence[-1]
            return current_context + f"\n\nLatest finding: {latest.snippet[:200]}"
        return current_context

    def _build_result(self, error: str | None = None) -> AgentResult:
        """Build typed result. Subclasses override to add domain output."""
        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self.AGENT_TYPE,
            success=error is None,
            evidence_items=self._evidence,
            derived_insights=self._insights,
            summary=self._build_summary(),
            error=error,
        )

    def _build_summary(self) -> str:
        """Human-readable summary. Subclasses should override."""
        return (
            f"{self.AGENT_TYPE}: {self._steps_taken} steps, "
            f"{len(self._evidence)} evidence, "
            f"{len(self._insights)} insights"
        )

    def _emit_step(
        self, step: int, thought: AgentThought, observation: str
    ) -> None:
        emit(self._run_id, EventType.AGENT_COMPLETED, {
            "agent_id": self._agent_id,
            "step": step,
            "action": thought.action,
            "query": thought.query[:200] if thought.query else "",
            "reasoning": thought.reasoning[:200] if thought.reasoning else "",
            "observation_preview": str(observation)[:200],
        })

    def get_agent_state(self) -> AgentState:
        """Snapshot of current agent state for run tracking."""
        return AgentState(
            agent_id=self._agent_id,
            agent_type=self.AGENT_TYPE,
            status="completed" if self._steps_taken > 0 else "pending",
            tool_calls_made=self._budget.total_tool_calls_used,
            tool_calls_budget=self.MAX_STEPS,
            evidence_produced=[e.evidence_id for e in self._evidence],
            summary=self._build_summary(),
        )
