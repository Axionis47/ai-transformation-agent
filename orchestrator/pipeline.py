"""Pipeline orchestrator — chains agents and runs end-to-end (7 stages)."""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from agents.base import AgentError, BaseAgent
from agents.consultant import ConsultantAgent
from agents.maturity_scorer import MaturityScorerAgent
from agents.rag_query import RAGQueryAgent
from agents.report_writer import ReportWriterAgent
from agents.scraper import ScraperAgent
from agents.signal_extractor import SignalExtractorAgent
from agents.use_case_generator import UseCaseGeneratorAgent
from ops.logger import PipelineLogger, get_logger
from orchestrator.gates import scraper_quality_gate
from orchestrator.state import PipelineState, PipelineStatus
from orchestrator.validators import validate_maturity, validate_signals, validate_use_cases
from orchestrator.victory_matcher import match_victories
from rag.ingest import ensure_seeds_loaded

_STAGE_TIMEOUT_S = 60
_COST_CONSULTANT = 0.005
_COST_SIGNAL = 0.001
_COST_MATURITY = 0.001
_COST_USE_CASE = 0.005
_COST_REPORT = 0.004


def _run_with_timeout(agent: BaseAgent, input_data: dict, timeout: int = _STAGE_TIMEOUT_S) -> object:
    """Run agent.run(input_data) in a thread; return AgentError on timeout."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(agent.run, input_data)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeout:
            return AgentError(
                code="TIMEOUT",
                message=f"{agent.agent_tag} exceeded {timeout}s",
                recoverable=False,
                agent_tag=agent.agent_tag,
            )


def _log_stage(logger: PipelineLogger, tag: str, event: str, **kwargs: object) -> None:
    logger.log(tag, event, **kwargs)


def _fail(state: PipelineState, error: AgentError, start: float,
          logger: PipelineLogger | None = None) -> PipelineState:
    state.status = PipelineStatus.FAILED
    state.error = {"code": error.code, "message": error.message, "agent": error.agent_tag}
    state.elapsed_seconds = round(time.time() - start, 2)
    if logger:
        logger.log("PIPELINE", "failed", error=state.error, elapsed_seconds=state.elapsed_seconds)
    return state


def run_pipeline(url: str, dry_run: bool = False) -> PipelineState:
    """Execute the full pipeline: scrape -> RAG -> consult -> report."""
    os.environ["DRY_RUN"] = "true" if dry_run else "false"

    if not dry_run:
        ensure_seeds_loaded()

    state = PipelineState(url=url, dry_run=dry_run)
    state.status = PipelineStatus.RUNNING
    start = time.time()
    logger: PipelineLogger = get_logger(state.run_id)

    # Stage 1: Scrape
    t = time.time()
    _log_stage(logger, "SCRAPER", "start", prompt_file="prompts/scraper.md", prompt_version="1.0")
    result = _run_with_timeout(ScraperAgent(), {"url": state.url})
    if isinstance(result, AgentError):
        _log_stage(logger, "SCRAPER", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.company_data = result
    _log_stage(logger, "SCRAPER", "complete", elapsed_ms=int((time.time() - t) * 1000))

    # Gate: reject thin or error-page content before expensive stages
    if not dry_run:
        passed, reason = scraper_quality_gate(state.company_data)
        if not passed:
            _log_stage(logger, "GATE", "scraper_quality_fail", reason=reason)
            return _fail(state, AgentError(
                code="SCRAPE_THIN", message=reason,
                recoverable=False, agent_tag="SCRAPER"
            ), start, logger)

    # Stage 2: RAG query
    t = time.time()
    _log_stage(logger, "RAG", "start", prompt_file="prompts/rag_query.md", prompt_version="1.0")
    result = _run_with_timeout(RAGQueryAgent(), {"company_data": state.company_data})
    if isinstance(result, AgentError):
        _log_stage(logger, "RAG", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.rag_context = result
    _log_stage(logger, "RAG", "complete", elapsed_ms=int((time.time() - t) * 1000))

    # Stage 3: Consultant analysis
    t = time.time()
    _log_stage(logger, "CONSULTANT", "start", prompt_file="prompts/consultant.md", prompt_version="1.0")
    result = _run_with_timeout(ConsultantAgent(), {"company_data": state.company_data, "rag_context": state.rag_context})
    if isinstance(result, AgentError):
        _log_stage(logger, "CONSULTANT", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.analysis = result
    if not dry_run:
        state.cost_usd += _COST_CONSULTANT
    _log_stage(logger, "CONSULTANT", "complete", elapsed_ms=int((time.time() - t) * 1000))

    # Stage 4: Report generation
    t = time.time()
    _log_stage(logger, "REPORT_WRITER", "start", prompt_file="prompts/report_writer.md", prompt_version="1.0")
    result = _run_with_timeout(ReportWriterAgent(), {"analysis": state.analysis})
    if isinstance(result, AgentError):
        _log_stage(logger, "REPORT_WRITER", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.report = result
    if not dry_run:
        state.cost_usd += _COST_REPORT
    _log_stage(logger, "REPORT_WRITER", "complete", elapsed_ms=int((time.time() - t) * 1000))

    state.status = PipelineStatus.COMPLETE
    state.elapsed_seconds = round(time.time() - start, 2)
    mode = "dry-run" if dry_run else "live"
    logger.log("PIPELINE", "complete", elapsed_seconds=state.elapsed_seconds,
               cost_usd=state.cost_usd, mode=mode)

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
