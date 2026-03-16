"""Per-stage I/O summary builders for pipeline logging."""

from __future__ import annotations

from typing import Any


def scraper_input(url: str) -> dict[str, Any]:
    return {"url": url}


def scraper_output(company_data: Any) -> dict[str, Any]:
    pages = list(company_data.keys()) if isinstance(company_data, dict) else []
    total_chars = sum(len(str(v)) for v in company_data.values()) if isinstance(company_data, dict) else 0
    return {"pages_fetched": len(pages), "total_chars": total_chars}


def signal_input(company_data: Any) -> dict[str, Any]:
    content_len = sum(len(str(v)) for v in company_data.values()) if isinstance(company_data, dict) else 0
    pages = len(company_data) if isinstance(company_data, dict) else 0
    return {"content_length": content_len, "pages": pages}


def signal_output(signals: dict[str, Any] | None) -> dict[str, Any]:
    s = signals or {}
    return {
        "signal_count": len(s.get("signals", [])),
        "confidence_level": s.get("confidence_level"),
        "industry": s.get("industry"),
        "scale": s.get("scale"),
    }


def maturity_input(signals: dict[str, Any] | None) -> dict[str, Any]:
    return {"signal_count": len((signals or {}).get("signals", []))}


def maturity_output(maturity: dict[str, Any] | None) -> dict[str, Any]:
    m = maturity or {}
    dims = m.get("dimensions") or {}
    dim_scores = {k: v.get("score") for k, v in dims.items()} if dims else {}
    return {
        "composite_score": m.get("composite_score"),
        "composite_label": m.get("composite_label"),
        "dimension_scores": dim_scores,
    }


def rag_input(signals: dict[str, Any] | None, company_data: Any) -> dict[str, Any]:
    industry = (signals or {}).get("industry", "unknown")
    preview = str(company_data)[:100] if company_data else ""
    return {"industry": industry, "query_text_preview": preview}


def rag_output(rag_context: list | None) -> dict[str, Any]:
    return {"match_count": len(rag_context) if rag_context else 0}


def victory_input(rag_context: list | None, maturity: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "match_count": len(rag_context) if rag_context else 0,
        "composite_score": (maturity or {}).get("composite_score"),
    }


def victory_output(victory_matches: list[dict[str, Any]]) -> dict[str, Any]:
    top = victory_matches[0] if victory_matches else {}
    return {
        "match_count": len(victory_matches),
        "top_match_win_id": top.get("win_id"),
        "top_match_tier": top.get("tier"),
    }


def use_case_input(signals: dict[str, Any] | None, maturity: dict[str, Any] | None,
                   victory_matches: list | None) -> dict[str, Any]:
    return {
        "signal_count": len((signals or {}).get("signals", [])),
        "maturity_label": (maturity or {}).get("composite_label", "unknown"),
        "match_count": len(victory_matches) if victory_matches else 0,
    }


def use_case_output(use_cases: list[dict[str, Any]]) -> dict[str, Any]:
    tiers = list({uc.get("tier") for uc in use_cases if uc.get("tier")})
    return {"use_case_count": len(use_cases), "tiers": tiers}


def report_writer_input(sections: list[str]) -> dict[str, Any]:
    return {"section_count": len(sections)}


def report_writer_output(report: dict[str, Any] | None, sections: list[str]) -> dict[str, Any]:
    present = [s for s in sections if report and report.get(s)]
    total_chars = sum(len(str(v)) for v in (report or {}).values())
    return {"sections_present": present, "total_chars": total_chars}
