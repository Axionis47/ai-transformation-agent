from __future__ import annotations

from core.schemas import Assumption, AssumptionsDraft, EvidenceItem

ASSUMPTION_FIELDS: list[tuple[str, str]] = [
    ("company_description", "What the company does"),
    ("industry_segment", "Specific industry segment"),
    ("company_size", "Approximate company size"),
    ("key_products", "Main products or services"),
    ("technology_stack", "Technology landscape"),
    ("business_model", "How the company makes money"),
]

ASSUMPTION_KEYWORDS: dict[str, list[str]] = {
    "company_description": ["company", "provides", "offers", "specializes", "founded", "operates"],
    "industry_segment": ["segment", "sector", "vertical", "niche", "division"],
    "company_size": ["employees", "staff", "headcount", "workforce", "team", "revenue", "million", "billion"],
    "key_products": ["product", "service", "platform", "solution", "tool", "software"],
    "technology_stack": ["technology", "platform", "software", "cloud", "infrastructure", "system"],
    "business_model": ["revenue", "subscription", "saas", "fee", "license", "model", "charges"],
}


def extract_assumptions(
    grounding_text: str,
    evidence_items: list[EvidenceItem],
) -> AssumptionsDraft:
    """Parse grounding response into structured assumptions.

    For each field, searches sentences for relevant keywords. Matched sentences
    become Assumption objects. Unmatched fields become open_questions.
    """
    avg_confidence = (
        sum(e.confidence_score for e in evidence_items if e.confidence_score is not None)
        / max(1, sum(1 for e in evidence_items if e.confidence_score is not None))
        if evidence_items else 0.5
    )
    if avg_confidence == 0.0:
        avg_confidence = 0.5

    sentences = [s.strip() for s in grounding_text.replace("\n", ". ").split(".") if s.strip()]
    assumptions: list[Assumption] = []
    open_questions: list[str] = []

    for field_name, description in ASSUMPTION_FIELDS:
        keywords = ASSUMPTION_KEYWORDS[field_name]
        matched: str | None = None
        for sentence in sentences:
            lower = sentence.lower()
            if any(kw in lower for kw in keywords):
                matched = sentence
                break
        if matched:
            assumptions.append(
                Assumption(
                    field=field_name,
                    value=matched,
                    confidence=round(avg_confidence, 4),
                    source="grounding",
                )
            )
        else:
            open_questions.append(description)

    return AssumptionsDraft(assumptions=assumptions, open_questions=open_questions)
