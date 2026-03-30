"""Working memory — maintains per-field synthesized knowledge across loops.

Instead of handing the LLM a growing pile of raw evidence, working memory
maintains a structured brief: one synthesis per required field, updated
after each loop. This keeps prompt size constant while depth increases.
"""

from __future__ import annotations

from core.schemas import EvidenceItem, FieldKnowledge
from engines.thought.mid import REQUIRED_FIELDS


class WorkingMemory:
    """Structured research state that grows in quality, not size."""

    def __init__(self) -> None:
        self._fields: dict[str, FieldKnowledge] = {f: FieldKnowledge(field=f) for f in REQUIRED_FIELDS}
        self._hypotheses: list[str] = []

    def get_field(self, field: str) -> FieldKnowledge:
        return self._fields.get(field, FieldKnowledge(field=field))

    def get_all_fields(self) -> dict[str, FieldKnowledge]:
        return dict(self._fields)

    def update_field(
        self, field: str, synthesis: str, evidence_ids: list[str], confidence: float, loop_idx: int
    ) -> None:
        """Update a field's synthesis after new evidence is processed."""
        fk = self._fields.get(field)
        if not fk:
            fk = FieldKnowledge(field=field)
            self._fields[field] = fk
        fk.synthesis = synthesis
        # Merge evidence IDs, don't replace
        existing = set(fk.evidence_ids)
        fk.evidence_ids = list(existing | set(evidence_ids))
        fk.confidence = confidence
        fk.last_updated_loop = loop_idx

    def add_hypothesis(self, hypothesis: str) -> None:
        if hypothesis not in self._hypotheses:
            self._hypotheses.append(hypothesis)

    @property
    def hypotheses(self) -> list[str]:
        return list(self._hypotheses)

    def build_briefing(self) -> str:
        """Build the structured briefing for the LLM prompt."""
        lines: list[str] = []
        for field in REQUIRED_FIELDS:
            fk = self._fields[field]
            label = field.replace("_", " ").upper()
            conf_pct = f"{fk.confidence * 100:.0f}%" if fk.confidence > 0 else "—"
            src_count = len(fk.evidence_ids)
            if fk.synthesis:
                lines.append(f"{label} [{conf_pct} confidence, {src_count} sources]:")
                lines.append(f"  {fk.synthesis}")
            else:
                lines.append(f"{label} [not yet researched]")
            lines.append("")
        if self._hypotheses:
            lines.append("WORKING HYPOTHESES:")
            for h in self._hypotheses:
                lines.append(f"  - {h}")
        return "\n".join(lines)

    def classify_evidence(self, evidence: list[EvidenceItem]) -> dict[str, list[EvidenceItem]]:
        """Group evidence items by which field they most likely cover."""
        from engines.thought.mid import _FIELD_SIGNALS

        result: dict[str, list[EvidenceItem]] = {f: [] for f in REQUIRED_FIELDS}
        for ev in evidence:
            text = f"{ev.title} {ev.snippet}".lower()
            best_field = ""
            best_hits = 0
            for field, signals in _FIELD_SIGNALS.items():
                hits = sum(1 for s in signals if s in text)
                if hits > best_hits:
                    best_hits = hits
                    best_field = field
            if best_field:
                result[best_field].append(ev)
            else:
                # Default to company_profile if no signals match
                result["company_profile"].append(ev)
        return result
