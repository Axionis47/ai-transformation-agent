from __future__ import annotations

from dataclasses import dataclass, field

from core.schemas import EvidenceItem, EvidenceSource
from engines.pitch.templates import OpportunityTemplate


@dataclass
class TemplateMatch:
    template: OpportunityTemplate
    match_score: float
    win_signal_hits: list[str]
    anti_signal_hits: list[str]
    matched_evidence_ids: list[str]
    matched_engagement_ids: list[str]


def match_templates(
    evidence: list[EvidenceItem],
    templates: list[OpportunityTemplate],
) -> list[TemplateMatch]:
    """Score each template against accumulated evidence using signal keywords."""
    matches: list[TemplateMatch] = []

    for tmpl in templates:
        win_hits: list[str] = []
        anti_hits: list[str] = []
        matched_evidence_ids: list[str] = []
        matched_engagement_ids: list[str] = []

        for item in evidence:
            text = (item.title + " " + item.snippet).lower()
            item_contributed = False

            for signal in tmpl.win_signals:
                if signal.lower() in text and signal not in win_hits:
                    win_hits.append(signal)
                    item_contributed = True

            for signal in tmpl.anti_signals:
                if signal.lower() in text and signal not in anti_hits:
                    anti_hits.append(signal)

            if item_contributed and item.evidence_id not in matched_evidence_ids:
                matched_evidence_ids.append(item.evidence_id)

            # Track engagement_ids from WINS_KB evidence
            if (
                item.source_type == EvidenceSource.WINS_KB
                and item.source_ref
                and item.source_ref not in matched_engagement_ids
                and item_contributed
            ):
                matched_engagement_ids.append(item.source_ref)

        n_signals = len(tmpl.win_signals)
        n_anti = max(len(tmpl.anti_signals), 1)
        raw = len(win_hits) / n_signals - 0.5 * len(anti_hits) / n_anti
        score = max(0.0, min(1.0, raw))

        if score > 0.1:
            matches.append(
                TemplateMatch(
                    template=tmpl,
                    match_score=round(score, 4),
                    win_signal_hits=win_hits,
                    anti_signal_hits=anti_hits,
                    matched_evidence_ids=matched_evidence_ids,
                    matched_engagement_ids=matched_engagement_ids,
                )
            )

    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches
