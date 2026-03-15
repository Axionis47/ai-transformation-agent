"""Pipeline quality gates — deterministic checks between stages."""

from __future__ import annotations

_ERROR_SIGNALS = [
    "404 not found",
    "access denied",
    "page not found",
    "403 forbidden",
    "robot",
    "captcha",
    "cloudflare",
]


def scraper_quality_gate(company_data: dict) -> tuple[bool, str]:
    """Check scraped content quality. Returns (passed, reason)."""
    if not company_data:
        return False, "Scraper returned empty data."

    text_fields = []
    for key in ("about_text", "product_text", "careers_text"):
        val = company_data.get(key, "")
        if val:
            text_fields.append(val)

    postings = company_data.get("job_postings", [])
    if isinstance(postings, list):
        for p in postings:
            if isinstance(p, str):
                text_fields.append(p)

    combined = " ".join(text_fields)
    word_count = len(combined.split())

    if word_count < 50:
        return False, (
            f"Scraped content too thin ({word_count} words). "
            "The website may be blocking automated access or the URL may be incorrect."
        )

    lower = combined.lower()
    for signal in _ERROR_SIGNALS:
        if signal in lower and word_count < 200:
            return False, (
                f"Scraped content appears to be an error page (detected '{signal}'). "
                "Try linking to the company's About or Careers page directly."
            )

    has_about = bool(company_data.get("about_text", "").strip())
    has_postings = bool(postings)
    if not has_about and not has_postings:
        return False, (
            "No about page content or job postings found. "
            "The analysis needs at least one of these to produce reliable results."
        )

    return True, ""
