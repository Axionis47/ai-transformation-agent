"""Aggregate metrics computation for eval results."""

from __future__ import annotations

from dataclasses import dataclass, field

from evals.eval_runner import EvalResult


@dataclass
class AggregateMetrics:
    total_runs: int
    successful_runs: int
    success_rate: float
    avg_evidence_count: float
    avg_opportunity_count: float
    avg_confidence: float
    avg_coverage: float
    budget_adherence_rate: float
    avg_latency_seconds: float
    tier_totals: dict[str, int]
    industry_breakdown: dict[str, dict] = field(default_factory=dict)


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _avg_coverage(field_coverage: dict[str, float]) -> float:
    vals = list(field_coverage.values())
    return _avg(vals) if vals else 0.0


def compute_metrics(results: list[EvalResult]) -> AggregateMetrics:
    """Compute aggregate metrics across all eval results."""
    if not results:
        return AggregateMetrics(
            total_runs=0,
            successful_runs=0,
            success_rate=0.0,
            avg_evidence_count=0.0,
            avg_opportunity_count=0.0,
            avg_confidence=0.0,
            avg_coverage=0.0,
            budget_adherence_rate=0.0,
            avg_latency_seconds=0.0,
            tier_totals={"easy": 0, "medium": 0, "hard": 0},
        )

    successes = [r for r in results if r.success]
    total = len(results)
    n_ok = len(successes)

    tier_totals: dict[str, int] = {"easy": 0, "medium": 0, "hard": 0}
    for r in successes:
        for tier, count in r.tier_distribution.items():
            tier_totals[tier] = tier_totals.get(tier, 0) + count

    industry_breakdown: dict[str, dict] = {}
    for r in results:
        ind = r.industry
        if ind not in industry_breakdown:
            industry_breakdown[ind] = {
                "total": 0,
                "success": 0,
                "avg_confidence": 0.0,
                "avg_opportunities": 0.0,
            }
        industry_breakdown[ind]["total"] += 1
        if r.success:
            industry_breakdown[ind]["success"] += 1

    for ind, stats in industry_breakdown.items():
        ind_successes = [r for r in successes if r.industry == ind]
        stats["avg_confidence"] = _avg([r.overall_confidence for r in ind_successes])
        stats["avg_opportunities"] = _avg([float(r.opportunity_count) for r in ind_successes])

    budget_ok = [r for r in results if r.budget_adherence]

    return AggregateMetrics(
        total_runs=total,
        successful_runs=n_ok,
        success_rate=round(n_ok / total, 4) if total else 0.0,
        avg_evidence_count=_avg([float(r.evidence_count) for r in successes]),
        avg_opportunity_count=_avg([float(r.opportunity_count) for r in successes]),
        avg_confidence=_avg([r.overall_confidence for r in successes]),
        avg_coverage=_avg([_avg_coverage(r.field_coverage) for r in successes]),
        budget_adherence_rate=round(len(budget_ok) / total, 4) if total else 0.0,
        avg_latency_seconds=_avg([r.latency_seconds for r in successes]),
        tier_totals=tier_totals,
        industry_breakdown=industry_breakdown,
    )


def format_report(metrics: AggregateMetrics) -> str:
    """Return a formatted text report of eval metrics."""
    lines = [
        "=" * 60,
        "  Eval Harness Report",
        "=" * 60,
        f"  Runs:              {metrics.total_runs} total / {metrics.successful_runs} successful",
        f"  Success rate:      {metrics.success_rate * 100:.1f}%",
        f"  Budget adherence:  {metrics.budget_adherence_rate * 100:.1f}%",
        f"  Avg evidence:      {metrics.avg_evidence_count:.1f} items",
        f"  Avg opportunities: {metrics.avg_opportunity_count:.1f}",
        f"  Avg confidence:    {metrics.avg_confidence:.3f}",
        f"  Avg coverage:      {metrics.avg_coverage:.3f}",
        f"  Avg latency:       {metrics.avg_latency_seconds:.2f}s",
        "",
        "  Tier distribution:",
        f"    Easy:   {metrics.tier_totals.get('easy', 0)}",
        f"    Medium: {metrics.tier_totals.get('medium', 0)}",
        f"    Hard:   {metrics.tier_totals.get('hard', 0)}",
        "",
        "  Industry breakdown:",
    ]
    for ind, stats in sorted(metrics.industry_breakdown.items()):
        ok = stats["success"]
        total = stats["total"]
        avg_conf = stats["avg_confidence"]
        avg_opps = stats["avg_opportunities"]
        lines.append(f"    {ind:<25} {ok}/{total} runs  conf={avg_conf:.3f}  opps={avg_opps:.1f}")
    lines.append("=" * 60)
    return "\n".join(lines)
