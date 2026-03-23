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


class FakeGeminiClient:
    """Test double for GeminiClient. Returns canned grounding responses."""

    def __init__(self, responses: list[dict] | None = None) -> None:
        self._queue: list[dict] = list(responses) if responses else []
        self.call_count: int = 0

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
