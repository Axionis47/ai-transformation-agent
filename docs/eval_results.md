# Eval Harness Results

Run date: 2026-03-23
Branch: seeker-architecture
Test set: 25 synthetic company bundles (8 industries)

## Results

```
Running eval harness for 25 company bundles...
============================================================
  Eval Harness Report
============================================================
  Runs:              25 total / 25 successful
  Success rate:      100.0%
  Budget adherence:  100.0%
  Avg evidence:      6.9 items
  Avg opportunities: 4.8
  Avg confidence:    0.749
  Avg coverage:      0.897
  Avg latency:       0.10s

  Tier distribution:
    Easy:   16
    Medium: 72
    Hard:   32

  Industry breakdown:
    education                 1/1 runs  conf=0.560  opps=3.0
    financial_services        5/5 runs  conf=0.766  opps=5.0
    healthcare                5/5 runs  conf=0.746  opps=5.0
    logistics                 4/4 runs  conf=0.732  opps=5.0
    manufacturing             4/4 runs  conf=0.772  opps=4.5
    professional_services     4/4 runs  conf=0.763  opps=5.0
    real_estate               1/1 runs  conf=0.769  opps=4.0
    retail                    1/1 runs  conf=0.757  opps=5.0
============================================================
```

## Metrics vs targets

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Coverage | > 70% | 89.7% | PASS |
| Budget adherence | > 95% | 100% | PASS |
| Latency | < 2 min | 0.10s | PASS |
| Opportunities generated | 3-5 per run | 4.8 avg | PASS |

## Notes

- 120 total opportunities across 25 runs: 16 Easy, 72 Medium, 32 Hard
- Known industries produce 4.5-5.0 opportunities per run
- Unseen industries (education, real_estate) still produce 3-4 opportunities from cross-industry template matching
- Budget adherence is 100%. No BUDGET_VIOLATION_BLOCKED events emitted in any run.
- Uses FakeGeminiClient with industry-aware canned responses + seeded RAG store

## How to reproduce

```bash
cd /Users/sid47/Desktop/ai-transformation-agent
python3 -m evals.run_eval
```
