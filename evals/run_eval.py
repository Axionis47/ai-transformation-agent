"""CLI entry point: run eval harness across all 25 company bundles and print metrics."""
from __future__ import annotations

import sys

from evals.eval_runner import run_all
from evals.metrics import compute_metrics, format_report


def main() -> None:
    print(f"Running eval harness for 25 company bundles...")
    results = run_all()
    metrics = compute_metrics(results)
    report = format_report(metrics)
    print(report)

    failures = [r for r in results if not r.success]
    if failures:
        print(f"\nFailed bundles ({len(failures)}):")
        for r in failures:
            print(f"  {r.company_name}: {r.error}")

    # Exit 1 if success rate is below 80%
    if metrics.success_rate < 0.80:
        sys.exit(1)


if __name__ == "__main__":
    main()
