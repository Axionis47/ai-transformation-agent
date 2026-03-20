"""RAG query agent — retrieves from both solution libraries (tenex_delivered + industry_cases)."""

from __future__ import annotations

import json
from pathlib import Path
from agents.base import AgentError, BaseAgent
from rag.vector_store import get_vector_store

_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rag_seeds"
_VICTORIES = _FIXTURES / "victories.json"
_INDUSTRY_CASES = _FIXTURES / "industry_cases.json"

# Fallback keyword detection when no signals are available
_INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "Logistics": ["logistics", "freight", "carrier", "shipping", "trucking", "fleet", "delivery", "supply chain", "warehouse"],
    "Healthcare": ["health", "hospital", "clinic", "medical", "patient", "pharma", "clinical", "care"],
    "Financial Services": ["financial", "finance", "bank", "insurance", "fintech", "lending", "credit", "investment"],
    "Retail": ["retail", "ecommerce", "e-commerce", "consumer", "store", "merchandise", "fulfillment"],
    "Manufacturing": ["manufacturing", "factory", "production", "industrial", "plant", "assembly", "machining"],
    "Technology": ["software", "saas", "platform", "tech", "developer", "cloud", "api", "data"],
}


class RAGQueryAgent(BaseAgent):
    """Queries both vector store collections for the three-tier matching layer.

    Returns dict with keys:
      delivered_results: list[dict]  -- from tenex_delivered collection (Library A)
      industry_results:  list[dict]  -- from industry_cases collection  (Library B)
    """

    agent_tag = "RAG"

    def _run(self, input_data: dict) -> dict[str, list[dict]] | AgentError:
        if self.dry_run:
            return self._dry_run_both()

        company_data = input_data.get("company_data", {})
        signals = input_data.get("signals")
        query_text = self._build_query(company_data, signals=signals)
        delivered_store = get_vector_store("tenex_delivered")
        industry_store = get_vector_store("industry_cases")
        delivered = delivered_store.query_all()
        industry = industry_store.query_all()
        if isinstance(delivered, AgentError):
            return delivered
        if isinstance(industry, AgentError):
            return industry
        return {"delivered_results": delivered, "industry_results": industry}

    def _dry_run_both(self) -> dict[str, list[dict]]:
        """Return fixture records for both collections in dry-run mode."""
        try:
            delivered = json.loads(_VICTORIES.read_text())
        except FileNotFoundError:
            delivered = [{"id": "win-000", "embed_text": "Mock: AI solution", "industry": "general"}]
        try:
            industry = json.loads(_INDUSTRY_CASES.read_text())
        except FileNotFoundError:
            industry = [{"id": "ind-000", "embed_text": "Mock industry case", "industry": "general"}]
        return {"delivered_results": delivered, "industry_results": industry}

    def _build_query(self, company_data: dict, signals: dict | None = None) -> str:
        """Build a structured query from signals (preferred) or keyword fallback."""
        about = company_data.get("about_text", "")
        profile_snippet = about[:300].strip() if about else "Company profile not available"

        if signals:
            industry = signals.get("industry", "Unknown")
            signal_list = signals.get("signals", [])
            pain_points = [
                s["value"] for s in signal_list
                if isinstance(s, dict) and s.get("dimension") == "pain_point"
            ]
            tech_stack = [
                s["value"] for s in signal_list
                if isinstance(s, dict) and s.get("dimension") == "tech_stack"
            ]
            pain_line = f"Pain points: {', '.join(pain_points)}" if pain_points else ""
            tech_line = f"Tech stack: {', '.join(tech_stack)}" if tech_stack else ""
            parts = [f"{industry} — {profile_snippet}"]
            if pain_line:
                parts.append(pain_line)
            if tech_line:
                parts.append(tech_line)
            parts.append("Looking for: applied AI solution with quantified results for similar company")
            return "\n\n".join(parts)

        # Fallback: keyword-based industry detection
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
        problem_line = f"Problem: {pain_hint}" if pain_hint else "Problem: operational inefficiency and manual processes"
        return (
            f"{industry} — {profile_snippet}\n\n"
            f"{problem_line}\n\n"
            "Looking for: similar Tenex delivery win with quantified results"
        )
