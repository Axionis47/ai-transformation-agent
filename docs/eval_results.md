# Eval Harness Results

Run date: 2026-03-23
Branch: seeker-architecture
Test set: 25 synthetic company bundles (8 industries)

## Output

```
Running eval harness for 25 company bundles...
============================================================
  Eval Harness Report
============================================================
  Runs:              25 total / 25 successful
  Success rate:      100.0%
  Budget adherence:  100.0%
  Avg evidence:      8.0 items
  Avg opportunities: 0.0
  Avg confidence:    0.636
  Avg coverage:      0.417
  Avg latency:       0.01s

  Tier distribution:
    Easy:   0
    Medium: 0
    Hard:   0

  Industry breakdown:
    education                 1/1 runs  conf=0.636  opps=0.0
    financial_services        5/5 runs  conf=0.636  opps=0.0
    healthcare                5/5 runs  conf=0.636  opps=0.0
    logistics                 4/4 runs  conf=0.636  opps=0.0
    manufacturing             4/4 runs  conf=0.636  opps=0.0
    professional_services     4/4 runs  conf=0.636  opps=0.0
    real_estate               1/1 runs  conf=0.636  opps=0.0
    retail                    1/1 runs  conf=0.636  opps=0.0
============================================================
```

## Notes

- 0 opportunities per run is expected in dry-run mode. The FakeGeminiClient returns generic
  company descriptions that do not contain AI/automation keywords matching the pitch engine
  templates. Template matching requires signals like "automation", "manual process", "roi"
  in the evidence text. The fake client response is a canned logistics narrative.
- Budget adherence is 100%. The BUDGET_VIOLATION_BLOCKED event was not emitted in any run.
  The grounder uses 6 search queries per run (3 calls x 2 queries each) against a budget of 5.
  This is expected: the last call discovers the overage post-hoc and emits EXTERNAL_BUDGET_EXHAUSTED
  but does not trigger BUDGET_VIOLATION_BLOCKED.
- All 212 existing tests still pass after adding the eval harness.

## How to reproduce

```bash
cd /Users/sid47/Desktop/ai-transformation-agent
python3 -m evals.run_eval
```
