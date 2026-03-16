"""RAG query agent — retrieves similar AI solutions from vector store."""

from __future__ import annotations

import json
from pathlib import Path
from agents.base import AgentError, BaseAgent
from rag.vector_store import get_vector_store

_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rag_seeds"
_VICTORIES = _FIXTURES / "victories.json"

# Industry keywords for query signal extraction
_INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "Logistics": ["logistics", "freight", "carrier", "shipping", "trucking", "fleet", "delivery", "supply chain", "warehouse"],
    "Healthcare": ["health", "hospital", "clinic", "medical", "patient", "pharma", "clinical", "care"],
    "Financial Services": ["financial", "finance", "bank", "insurance", "fintech", "lending", "credit", "investment"],
    "Retail": ["retail", "ecommerce", "e-commerce", "consumer", "store", "merchandise", "fulfillment"],
    "Manufacturing": ["manufacturing", "factory", "production", "industrial", "plant", "assembly", "machining"],
    "Technology": ["software", "saas", "platform", "tech", "developer", "cloud", "api", "data"],
}


class RAGQueryAgent(BaseAgent):
    """Queries vector store for similar AI transformation solutions."""

    agent_tag = "RAG"

    def _run(self, input_data: dict) -> list[dict] | AgentError:
        if self.dry_run:
            try:
                records = json.loads(_VICTORIES.read_text())
                return records[:3]
            except FileNotFoundError:
                return [{"id": "win-000", "embed_text": "Mock: AI solution", "industry": "general"}]

        company_data = input_data.get("company_data", {})
        query_text = self._build_query(company_data)
        store = get_vector_store()
        return store.query(query_text, k=3)

    def _build_query(self, company_data: dict) -> str:
        """Build a structured query using the victory embed_text template format."""
        about = company_data.get("about_text", "")
        postings = company_data.get("job_postings", [])
        combined_text = (about + " " + " ".join(postings[:3])).lower()

        industry = "Unknown"
        for label, keywords in _INDUSTRY_KEYWORDS.items():
            if any(kw in combined_text for kw in keywords):
                industry = label
                break

        pain_hint = ""
        if "manual" in combined_text or "inefficien" in combined_text:
            pain_hint = "manual processes and operational inefficiency"
        elif "cost" in combined_text or "spend" in combined_text:
            pain_hint = "cost reduction and spend optimisation"
        elif "growth" in combined_text or "scale" in combined_text:
            pain_hint = "scaling operations and accelerating growth"

        profile_snippet = about[:300].strip() if about else "Company profile not available"
        problem_line = f"Problem: {pain_hint}" if pain_hint else "Problem: operational inefficiency and manual processes"

        return (
            f"{industry} — {profile_snippet}\n\n"
            f"{problem_line}\n\n"
            "Looking for: similar Tenex delivery win with quantified results"
        )
