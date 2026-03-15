"""Pipeline orchestrator — chains agents and runs end-to-end."""

from __future__ import annotations

import argparse
import os
import sys
import time

from agents.base import AgentError
from agents.consultant import ConsultantAgent
from agents.rag_query import RAGQueryAgent
from agents.report_writer import ReportWriterAgent
from agents.scraper import ScraperAgent
from orchestrator.state import PipelineState, PipelineStatus
from rag.ingest import ensure_seeds_loaded


def run_pipeline(url: str, dry_run: bool = False) -> PipelineState:
    """Execute the full pipeline: scrape -> RAG -> consult -> report."""
    if dry_run:
        os.environ["DRY_RUN"] = "true"

    if not dry_run:
        ensure_seeds_loaded()

    state = PipelineState(url=url, dry_run=dry_run)
    state.status = PipelineStatus.RUNNING
    start = time.time()

    # Step 1: Scrape
    print(f"[pipeline] Run {state.run_id} | Scraping company data...")
    result = ScraperAgent().run(state)
    if isinstance(result, AgentError):
        return _fail(state, result, start)
    state.company_data = result

    # Step 2: RAG query
    print("[pipeline] Querying RAG for similar companies...")
    result = RAGQueryAgent().run(state)
    if isinstance(result, AgentError):
        return _fail(state, result, start)
    state.rag_context = result

    # Step 3: Consultant analysis
    print("[pipeline] Scoring AI maturity...")
    result = ConsultantAgent().run(state)
    if isinstance(result, AgentError):
        return _fail(state, result, start)
    state.analysis = result

    # Step 4: Report generation
    print("[pipeline] Writing 5-section report...")
    result = ReportWriterAgent().run(state)
    if isinstance(result, AgentError):
        return _fail(state, result, start)
    state.report = result

    state.status = PipelineStatus.COMPLETE
    state.elapsed_seconds = round(time.time() - start, 2)
    mode = "dry-run" if dry_run else "live"
    print(f"[pipeline] Complete in {state.elapsed_seconds}s | Cost: ${state.cost_usd:.2f} ({mode})")

    return state


def _fail(state: PipelineState, error: AgentError, start: float) -> PipelineState:
    state.status = PipelineStatus.FAILED
    state.error = {"code": error.code, "message": error.message, "agent": error.agent_tag}
    state.elapsed_seconds = round(time.time() - start, 2)
    print(f"[pipeline] FAILED: [{error.agent_tag}] {error.code} — {error.message}")
    return state


def print_report(state: PipelineState) -> None:
    """Print the report sections to stdout."""
    if not state.report:
        print("[pipeline] No report generated.")
        return

    sections = ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]
    for section in sections:
        title = section.replace("_", " ").upper()
        content = state.report.get(section, "N/A")
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Transformation Discovery Pipeline")
    parser.add_argument("--url", required=True, help="Company URL to analyze")
    parser.add_argument("--dry-run", action="store_true", help="Use fixture data, no API calls")
    args = parser.parse_args()

    state = run_pipeline(url=args.url, dry_run=args.dry_run)

    if state.status == PipelineStatus.COMPLETE:
        print_report(state)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
