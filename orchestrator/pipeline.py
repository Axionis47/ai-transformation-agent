"""Pipeline orchestrator — chains agents and runs end-to-end."""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from agents.base import AgentError, BaseAgent
from agents.consultant import ConsultantAgent
from agents.rag_query import RAGQueryAgent
from agents.report_writer import ReportWriterAgent
from agents.scraper import ScraperAgent
from ops.logger import PipelineLogger, get_logger
from orchestrator.gates import scraper_quality_gate
from orchestrator.state import PipelineState, PipelineStatus
from rag.ingest import ensure_seeds_loaded

_STAGE_TIMEOUT_S = 60
_COST_CONSULTANT = 0.005
_COST_REPORT = 0.004


def _run_with_timeout(agent: BaseAgent, state: PipelineState, timeout: int = _STAGE_TIMEOUT_S) -> object:
    """Run agent.run(state) in a thread; return AgentError on timeout."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(agent.run, state)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeout:
            return AgentError(
                code="TIMEOUT",
                message=f"{agent.agent_tag} exceeded {timeout}s",
                recoverable=False,
                agent_tag=agent.agent_tag,
            )


def run_pipeline(url: str, dry_run: bool = False) -> PipelineState:
    """Execute the full pipeline: scrape -> RAG -> consult -> report."""
    # Set DRY_RUN env var so agents pick up the mode
    os.environ["DRY_RUN"] = "true" if dry_run else "false"

    if not dry_run:
        ensure_seeds_loaded()

    state = PipelineState(url=url, dry_run=dry_run)
    state.status = PipelineStatus.RUNNING
    start = time.time()
    logger: PipelineLogger = get_logger(state.run_id)

    # Step 1: Scrape
    _stage_start = time.time()
    logger.log("SCRAPER", "start", prompt_file="prompts/scraper.md", prompt_version="1.0")
    result = _run_with_timeout(ScraperAgent(), state)
    if isinstance(result, AgentError):
        logger.log("SCRAPER", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.company_data = result
    logger.log("SCRAPER", "complete", elapsed_ms=int((time.time() - _stage_start) * 1000))

    # Gate: reject thin or error-page content before expensive stages
    if not dry_run:
        passed, reason = scraper_quality_gate(state.company_data)
        if not passed:
            logger.log("GATE", "scraper_quality_fail", reason=reason)
            return _fail(state, AgentError(
                code="SCRAPE_THIN", message=reason,
                recoverable=False, agent_tag="SCRAPER"
            ), start, logger)

    # Step 2: RAG query
    _stage_start = time.time()
    logger.log("RAG", "start", prompt_file="prompts/rag_query.md", prompt_version="1.0")
    result = _run_with_timeout(RAGQueryAgent(), state)
    if isinstance(result, AgentError):
        logger.log("RAG", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.rag_context = result
    logger.log("RAG", "complete", elapsed_ms=int((time.time() - _stage_start) * 1000))

    # Step 3: Consultant analysis
    _stage_start = time.time()
    logger.log("CONSULTANT", "start", prompt_file="prompts/consultant.md", prompt_version="1.0")
    result = _run_with_timeout(ConsultantAgent(), state)
    if isinstance(result, AgentError):
        logger.log("CONSULTANT", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.analysis = result
    if not dry_run:
        state.cost_usd += _COST_CONSULTANT
    logger.log("CONSULTANT", "complete", elapsed_ms=int((time.time() - _stage_start) * 1000),
               cost_usd=state.cost_usd)

    # Step 4: Report generation
    _stage_start = time.time()
    logger.log("REPORT_WRITER", "start", prompt_file="prompts/report_writer.md", prompt_version="1.0")
    result = _run_with_timeout(ReportWriterAgent(), state)
    if isinstance(result, AgentError):
        logger.log("REPORT_WRITER", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.report = result
    if not dry_run:
        state.cost_usd += _COST_REPORT
    logger.log("REPORT_WRITER", "complete", elapsed_ms=int((time.time() - _stage_start) * 1000),
               cost_usd=state.cost_usd)

    state.status = PipelineStatus.COMPLETE
    state.elapsed_seconds = round(time.time() - start, 2)
    mode = "dry-run" if dry_run else "live"
    logger.log("PIPELINE", "complete", elapsed_seconds=state.elapsed_seconds,
               cost_usd=state.cost_usd, mode=mode)

    return state


def _fail(state: PipelineState, error: AgentError, start: float,
          logger: PipelineLogger | None = None) -> PipelineState:
    state.status = PipelineStatus.FAILED
    state.error = {"code": error.code, "message": error.message, "agent": error.agent_tag}
    state.elapsed_seconds = round(time.time() - start, 2)
    if logger:
        logger.log("PIPELINE", "failed", error=state.error, elapsed_seconds=state.elapsed_seconds)
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
