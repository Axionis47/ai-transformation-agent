from __future__ import annotations


_INDUSTRY_TEXT: dict[str, str] = {
    "logistics": (
        "The company operates a fleet of 500 vehicles for dispatch and routing. "
        "Manual scheduling of shipments is a costly bottleneck and the support team "
        "handles 400 customer service tickets per week about delivery status."
    ),
    "financial_services": (
        "The company processes 2000 transactions daily with manual compliance "
        "review for regulatory audit changes. Fraud detection is partially automated "
        "but analysts still review 600 flagged suspicious transactions per day."
    ),
    "healthcare": (
        "The company runs 12 outpatient clinics with scheduling problems and a "
        "30% no-show rate. Clinical documentation takes 45 minutes per patient. "
        "Insurance claims processing has a 14% error rate and costly rework."
    ),
    "manufacturing": (
        "The company runs CNC equipment with frequent unplanned downtime and "
        "maintenance challenges. Quality inspection defect detection takes 8 hours. "
        "Supplier risk monitoring relies on quarterly manual reviews."
    ),
    "retail": (
        "The company manages inventory across 40 locations with shrinkage issues. "
        "Demand forecasting is spreadsheet-based and inefficient. Customer support "
        "handles 200 returns per day through a manual ticket triage process."
    ),
    "professional_services": (
        "The company generates proposals and documentation manually taking 6 hours "
        "each. Resource allocation and staffing for projects is done in spreadsheets. "
        "Time tracking across 200 consultants is error-prone."
    ),
}


_REACT_RESPONSES: dict[int, dict] = {
    0: {
        "thinking": "Initial research found company overview but we lack specific pain points and operational challenges. Need to understand their workflows.",
        "action": "GROUND",
        "query": "What are the main operational challenges and inefficiencies?",
        "target_field": "pain_points",
        "reasoning": "Pain points are critical for matching AI opportunities to real problems.",
    },
    1: {
        "thinking": "We have company profile and pain points. Now need similar past engagements to ground recommendations in proven results.",
        "action": "RAG",
        "query": "automation implementation mid-market",
        "target_field": "similar_wins",
        "reasoning": "Past engagement data strengthens our recommendations with proven ROI.",
    },
    2: {
        "thinking": "We have good coverage across most fields. Evidence is sufficient to proceed to synthesis.",
        "action": "STOP",
        "query": "",
        "target_field": "",
        "reasoning": "Enough evidence across company profile, pain points, and similar wins to generate recommendations.",
    },
}


class FakeGeminiClient:
    """Test double for GeminiClient. Returns canned grounding and reasoning responses."""

    def __init__(self, responses: list[dict] | None = None) -> None:
        self._queue: list[dict] = list(responses) if responses else []
        self.call_count: int = 0
        self._reason_count: int = 0

    def generate(self, prompt: str) -> dict:
        """Pure reasoning response for ReAct steps and evaluations."""
        self._reason_count += 1
        if "evaluate whether this opportunity" in prompt.lower():
            return {"text": FakeGeminiClient._fake_opportunity_eval(prompt)}
        if "extract structured assumptions" in prompt.lower():
            return {"text": FakeGeminiClient._fake_assumption_extraction(prompt)}
        # ReAct step
        idx = min(self._reason_count - 1, 2)
        react = _REACT_RESPONSES.get(idx, _REACT_RESPONSES[2])
        import json
        return {"text": json.dumps(react)}

    def generate_with_grounding(self, prompt: str) -> dict:
        self.call_count += 1
        if self._queue:
            return self._queue.pop(0)
        return FakeGeminiClient.default_response(prompt)

    @staticmethod
    def _pick_text(prompt: str) -> str:
        lower = prompt.lower()
        for industry, text in _INDUSTRY_TEXT.items():
            if industry.replace("_", " ") in lower or industry in lower:
                return text
        return (
            "The company is mid-market with manual workflows across support, "
            "operations, and compliance. Processes are bottleneck-prone."
        )

    @staticmethod
    def _fake_assumption_extraction(prompt: str) -> str:
        import json
        return json.dumps({
            "assumptions": [
                {"field": "company_description", "value": "Mid-market company with manual workflows across support and operations", "confidence": 0.8, "confidence_reasoning": "Grounding text directly describes company operations", "source_quote": "operates with manual workflows"},
                {"field": "industry_segment", "value": "Core operations within the industry vertical", "confidence": 0.7, "confidence_reasoning": "Industry identified from grounding", "source_quote": "industry segment identified"},
                {"field": "company_size", "value": "Mid-market, estimated 200-2000 employees", "confidence": 0.5, "confidence_reasoning": "Inferred from operational scale", "source_quote": "mid-market scale"},
            ],
            "open_questions": [
                {"field": "key_products", "reason": "No specific product details in research", "suggested_query": "What products does the company offer?"},
                {"field": "technology_stack", "reason": "No technology details found", "suggested_query": "What technology platforms does the company use?"},
                {"field": "business_model", "reason": "Revenue model not described", "suggested_query": "How does the company generate revenue?"},
            ],
        })

    @staticmethod
    def _fake_opportunity_eval(prompt: str) -> str:
        import json
        return json.dumps({
            "fit_score": 0.65,
            "tier": "MEDIUM",
            "reasoning": "Evidence suggests operational inefficiencies that this template addresses, but industry-specific validation is limited.",
            "supporting_evidence_ids": [],
            "matched_engagement_ids": [],
            "risks": ["Limited industry-specific evidence", "Scale assumptions need validation"],
            "adaptation_needed": "Industry-specific workflows may require customization of the standard approach.",
            "feasibility": 0.7,
            "roi_score": 0.6,
            "time_to_value": 0.7,
            "confidence": 0.55,
            "rationale": "The company shows patterns consistent with this opportunity but requires adaptation for their specific context.",
        })

    @staticmethod
    def default_response(prompt: str) -> dict:
        text = FakeGeminiClient._pick_text(prompt)
        return {
            "text": text,
            "grounding_metadata": {
                "web_search_queries": ["company profile", "industry trends"],
                "grounding_chunks": [
                    {"web": {"uri": "https://example.com/about", "title": "Company Overview"}},
                    {"web": {"uri": "https://example.com/industry", "title": "Industry Analysis"}},
                ],
                "grounding_supports": [
                    {
                        "segment": {"text": text[:120]},
                        "grounding_chunk_indices": [0],
                        "confidence_scores": [0.90],
                    },
                    {
                        "segment": {"text": text[120:]},
                        "grounding_chunk_indices": [1],
                        "confidence_scores": [0.85],
                    },
                ],
                "search_entry_point": {
                    "rendered_content": "<style>.search-entry{}</style><div>Search</div>"
                },
            },
        }
