"""Persists derived insights and inter-phase briefings.

Not raw evidence (that's EvidenceStore), not hypotheses (that's HypothesisTracker).
This stores conclusions drawn from evidence: "A + B + C means Y".
Later agents read insights instead of re-deriving from raw evidence.
"""

from __future__ import annotations

from core.schemas import DerivedInsight

_insights: dict[str, list[DerivedInsight]] = {}  # run_id -> insights
_briefings: dict[str, dict[str, str]] = {}  # run_id -> {phase -> briefing}
_singleton: SynthesisStore | None = None


def get_synthesis_store() -> SynthesisStore:
    global _singleton
    if _singleton is None:
        _singleton = SynthesisStore()
    return _singleton


class SynthesisStore:
    """In-memory store for derived insights and phase briefings."""

    def save_insight(self, run_id: str, insight: DerivedInsight) -> None:
        if run_id not in _insights:
            _insights[run_id] = []
        # Dedup by insight_id
        existing_ids = {i.insight_id for i in _insights[run_id]}
        if insight.insight_id not in existing_ids:
            _insights[run_id].append(insight)

    def save_insights(self, run_id: str, insights: list[DerivedInsight]) -> None:
        for insight in insights:
            self.save_insight(run_id, insight)

    def get_insights(self, run_id: str, phase: str | None = None) -> list[DerivedInsight]:
        all_insights = _insights.get(run_id, [])
        if phase is not None:
            return [i for i in all_insights if i.phase == phase]
        return list(all_insights)

    def save_phase_briefing(self, run_id: str, phase: str, briefing: str) -> None:
        if run_id not in _briefings:
            _briefings[run_id] = {}
        _briefings[run_id][phase] = briefing

    def get_phase_briefing(self, run_id: str, phase: str) -> str | None:
        return _briefings.get(run_id, {}).get(phase)

    def get_all_briefings(self, run_id: str) -> dict[str, str]:
        return dict(_briefings.get(run_id, {}))

    def clear(self, run_id: str) -> None:
        _insights.pop(run_id, None)
        _briefings.pop(run_id, None)
