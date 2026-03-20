"""Pipeline orchestrator — chains agents and runs end-to-end (7 stages)."""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from agents.base import AgentError, BaseAgent
from agents.maturity_scorer import MaturityScorerAgent
from agents.rag_query import RAGQueryAgent
from agents.report_writer import ReportWriterAgent
from agents.signal_extractor import SignalExtractorAgent
from agents.use_case_generator import UseCaseGeneratorAgent
from orchestrator.schemas import UserHints
from orchestrator.signal_merger import merge_signals
from orchestrator.tool_registry import registry
from ops.logger import PipelineLogger, get_logger
from orchestrator.gates import scraper_quality_gate
from orchestrator.stage_io import (
    matching_output, maturity_input, maturity_output, rag_input, rag_output,
    report_writer_output, scraper_input, scraper_output,
    signal_input, signal_output, use_case_input, use_case_output,
    victory_input,
)
from orchestrator.state import PipelineState, PipelineStatus
from orchestrator.validators import validate_maturity, validate_signals, validate_use_cases
from orchestrator.victory_matcher import get_full_match_results, match_victories
from rag.ingest import ensure_seeds_loaded

_STAGE_TIMEOUT_S = 60
_COST_SIGNAL = 0.001
_COST_MATURITY = 0.001
_COST_USE_CASE = 0.005
_COST_REPORT = 0.004
_REPORT_SECTIONS = ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]


def _run_with_timeout(agent: BaseAgent, input_data: dict, timeout: int = _STAGE_TIMEOUT_S) -> object:
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


def _parallel_report_sections(
    analysis: dict, logger: PipelineLogger
) -> dict | AgentError:
    """Generate all 5 report sections concurrently (max 3 workers).

    Returns a dict of section_name -> content.
    If any section fails, that key is set to None.
    Falls back to single-call ReportWriterAgent on unexpected executor error.
    """
    agent = ReportWriterAgent()

    def _generate(section: str) -> tuple[str, str | None]:
        result = agent.generate_section(section, analysis)
        if isinstance(result, AgentError):
            logger.log("REPORT_WRITER", "section_error",
                       section=section, code=result.code, message=result.message)
            return section, None
        return section, result

    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(_generate, s): s for s in _REPORT_SECTIONS}
            report: dict = {}
            for future in futures:
                section_name, content = future.result(timeout=_STAGE_TIMEOUT_S)
                report[section_name] = content
    except Exception as exc:  # unexpected executor failure — fall back
        logger.log("REPORT_WRITER", "parallel_fallback", reason=str(exc))
        return _run_with_timeout(ReportWriterAgent(), {"analysis": analysis})

    return report


def run_pipeline(
    url: str,
    dry_run: bool = False,
    user_hints: dict | None = None,
) -> PipelineState:
    """Execute the 7-stage AI transformation pipeline."""
    os.environ["DRY_RUN"] = "true" if dry_run else "false"
    if not dry_run:
        ensure_seeds_loaded()

    _hints: UserHints | None = None
    if user_hints:
        try:
            _hints = UserHints(**user_hints)
        except Exception:
            _hints = None  # invalid hints — proceed without them

    state = PipelineState(
        url=url,
        dry_run=dry_run,
        user_hints=user_hints if _hints else None,
        has_user_hints=(_hints is not None),
    )
    state.status = PipelineStatus.RUNNING
    start = time.time()
    logger: PipelineLogger = get_logger(state.run_id)

    # Stage 1: Scrape
    t = time.time()
    logger.log_agent_call("SCRAPER", prompt_file="prompts/scraper.md", prompt_version="1.0",
                          input_summary=scraper_input(state.url))
    scraper_tool = registry.get("website_scraper")
    result = scraper_tool.run({"url": state.url, "dry_run": dry_run})
    if isinstance(result, AgentError):
        _log_stage(logger, "SCRAPER", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    state.company_data = result
    state.pages_fetched = result.get("pages_fetched") if isinstance(result, dict) else None
    logger.log_agent_call("SCRAPER", result=True, start_time=t,
                          prompt_file="prompts/scraper.md", prompt_version="1.0",
                          output_summary=scraper_output(state.company_data))

    if not dry_run:
        passed, reason = scraper_quality_gate(state.company_data)
        if not passed:
            _log_stage(logger, "GATE", "scraper_quality_fail", reason=reason)
            return _fail(state, AgentError(
                code="SCRAPE_THIN", message=reason,
                recoverable=False, agent_tag="SCRAPER"
            ), start, logger)

    # Stage 2: Signal extraction
    t = time.time()
    logger.log_agent_call("SIGNAL_EXTRACTOR", prompt_version="1.0",
                          input_summary=signal_input(state.company_data))
    result = _run_with_timeout(SignalExtractorAgent(), {"company_data": state.company_data})
    if isinstance(result, AgentError):
        _log_stage(logger, "SIGNAL_EXTRACTOR", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    validated = validate_signals(result)
    if isinstance(validated, AgentError):
        return _fail(state, validated, start, logger)
    merged = merge_signals(validated.model_dump(), _hints)
    state.signals = merged
    state.signal_count = len(merged.get("signals", []))
    if not dry_run:
        state.cost_usd += _COST_SIGNAL
    logger.log_agent_call("SIGNAL_EXTRACTOR", result=True, start_time=t, prompt_version="1.0",
                          output_summary=signal_output(state.signals))

    # Stage 3: Maturity scoring
    t = time.time()
    logger.log_agent_call("MATURITY_SCORER", prompt_version="1.0",
                          input_summary=maturity_input(state.signals))
    result = _run_with_timeout(MaturityScorerAgent(), {"signals": state.signals})
    if isinstance(result, AgentError):
        _log_stage(logger, "MATURITY_SCORER", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    validated = validate_maturity(result)
    if isinstance(validated, AgentError):
        return _fail(state, validated, start, logger)
    state.maturity = validated.model_dump()
    if not dry_run:
        state.cost_usd += _COST_MATURITY
    logger.log_agent_call("MATURITY_SCORER", result=True, start_time=t, prompt_version="1.0",
                          output_summary=maturity_output(state.maturity))

    # Stage 4: RAG query — returns both tenex_delivered and industry_cases results
    t = time.time()
    logger.log_agent_call("RAG", prompt_file="prompts/rag_query.md", prompt_version="1.0",
                          input_summary=rag_input(state.signals, state.company_data))
    result = _run_with_timeout(RAGQueryAgent(), {"company_data": state.company_data})
    if isinstance(result, AgentError):
        _log_stage(logger, "RAG", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    # result is dict with delivered_results + industry_results; keep rag_context for compat
    if isinstance(result, dict) and "delivered_results" in result:
        delivered_results = result.get("delivered_results", [])
        industry_results = result.get("industry_results", [])
        state.rag_context = delivered_results  # backwards compat
    else:
        delivered_results = result if isinstance(result, list) else []
        industry_results = []
        state.rag_context = delivered_results
    logger.log_agent_call("RAG", result=True, start_time=t,
                          prompt_file="prompts/rag_query.md", prompt_version="1.0",
                          output_summary=rag_output(result))

    # Stage 5: Matching layer — three-tier deterministic scoring
    logger.log_agent_call("VICTORY_MATCHER",
                          input_summary=victory_input(state.rag_context, state.maturity))
    three_tier = get_full_match_results(
        signals=state.signals or {},
        maturity=state.maturity or {},
        delivered_results=delivered_results,
        industry_results=industry_results,
    )
    state.match_results = {k: [mr.model_dump() for mr in v] for k, v in three_tier.items()}
    # Flatten delivered + adaptation into victory_matches for backwards compat
    flat = three_tier["delivered"] + three_tier["adaptation"]
    state.victory_matches = [mr.model_dump() for mr in flat] or [
        vm.model_dump() for vm in match_victories(
            signals_industry=(state.signals or {}).get("industry", "unknown"),
            signals_scale=(state.signals or {}).get("scale", "unknown"),
            maturity_label=(state.maturity or {}).get("composite_label", ""),
            rag_results=delivered_results,
        )
    ]
    logger.log_agent_call("VICTORY_MATCHER", result=True,
                          output_summary=matching_output(state.match_results))

    # Stage 6: Use case generation — per-tier synthesis using match_results
    t = time.time()
    logger.log_agent_call("USE_CASE_GENERATOR", prompt_version="1.0",
                          input_summary=use_case_input(state.signals, state.maturity, state.victory_matches))
    result = _run_with_timeout(UseCaseGeneratorAgent(), {
        "signals": state.signals,
        "maturity": state.maturity,
        "victory_matches": state.victory_matches,
        "match_results": state.match_results,
    })
    if isinstance(result, AgentError):
        _log_stage(logger, "USE_CASE_GENERATOR", "error", code=result.code, message=result.message)
        return _fail(state, result, start, logger)
    validated = validate_use_cases(result)
    if isinstance(validated, AgentError):
        return _fail(state, validated, start, logger)
    state.use_cases = [uc.model_dump() for uc in validated]
    if not dry_run:
        state.cost_usd += _COST_USE_CASE
    logger.log_agent_call("USE_CASE_GENERATOR", result=True, start_time=t, prompt_version="1.0",
                          output_summary=use_case_output(state.use_cases))

    # Build analysis for backward compat with app.py
    state.analysis = {
        "maturity_score": (state.maturity or {}).get("composite_score"),
        "maturity_label": (state.maturity or {}).get("composite_label"),
        "dimensions": (state.maturity or {}).get("dimensions"),
        "use_cases": state.use_cases,
    }

    # Stage 7: Report generation — parallel section writes
    t = time.time()
    logger.log("REPORT_WRITER", "report_parallel_start", sections=_REPORT_SECTIONS)
    analysis_payload = {
        "maturity_score": (state.maturity or {}).get("composite_score"),
        "maturity_label": (state.maturity or {}).get("composite_label"),
        "dimensions": (state.maturity or {}).get("dimensions"),
        "signals": state.signals, "use_cases": state.use_cases,
        "victory_matches": state.victory_matches,
    }
    report = _parallel_report_sections(analysis_payload, logger)
    if isinstance(report, AgentError):
        _log_stage(logger, "REPORT_WRITER", "error", code=report.code, message=report.message)
        return _fail(state, report, start, logger)
    state.report = report
    if not dry_run:
        state.cost_usd += _COST_REPORT
    elapsed_report = round(time.time() - t, 2)
    logger.log("REPORT_WRITER", "report_parallel_complete",
               elapsed_seconds=elapsed_report, sections_ok=list(report.keys()))
    logger.log_agent_call("REPORT_WRITER", result=True, start_time=t,
                          prompt_file="prompts/report_writer.md", prompt_version="1.0",
                          output_summary=report_writer_output(state.report, _REPORT_SECTIONS))

    state.status = PipelineStatus.COMPLETE
    state.elapsed_seconds = round(time.time() - start, 2)
    mode = "dry-run" if dry_run else "live"
    logger.log("PIPELINE", "complete", elapsed_seconds=state.elapsed_seconds,
               cost_usd=state.cost_usd, mode=mode)
    return state


def print_report(state: PipelineState) -> None:
    """Print report sections to stdout."""
    if not state.report:
        print("[pipeline] No report generated.")
        return
    for section in _REPORT_SECTIONS:
        title = section.replace("_", " ").upper()
        content = state.report.get(section, "N/A")
        print(f"\n{'='*60}\n  {title}\n{'='*60}\n{content}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Transformation Discovery Pipeline")
    parser.add_argument("--url", required=True, help="Company URL to analyze")
    parser.add_argument("--dry-run", action="store_true", help="Use fixture data, no API calls")
    args = parser.parse_args()
    state = run_pipeline(url=args.url, dry_run=args.dry_run)
    sys.exit(0 if state.status == PipelineStatus.COMPLETE else 1)


if __name__ == "__main__":
    main()
