# RAG Seeds — Victory Record Schema

This directory contains `victories.json`, the seeded dataset of 20 Tenex engagement
wins used to bootstrap the RAG vector store. Records are retrieved at query time
by the `rag_query` agent and passed to the use case generator as `victory_matches`.

---

## Schema Reference

Each victory record contains the following top-level fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier — format `win-NNN` |
| `engagement_title` | string | Short description of the engagement |
| `industry` | string | Primary industry vertical |
| `sector_tags` | array of strings | Sub-sector and capability tags for retrieval |
| `company_profile` | object | Size, revenue, geography, business model |
| `problem_statement` | string | Client's before-state — what was broken |
| `solution_summary` | string | What Tenex built and how it worked |
| `results` | object | `primary_metric` + `secondary_metrics` array |
| `engagement_details` | object | Duration, team size, roles, delivery model |
| `tech_stack` | object | Data sources, ML approach, infrastructure, integrations |
| `maturity_at_engagement` | string | Client's AI maturity label at start — see below |
| `follow_on_engagement` | boolean | Whether a follow-on engagement occurred |
| `lessons_learned` | string | Key insight for future engagements |
| `embed_text` | string | Flattened text used for vector embedding |

### Calibration Fields (added Sprint 5)

Three fields added to support use case generator calibration and ROI grounding:

| Field | Type | Description |
|-------|------|-------------|
| `industry_benchmark` | string | Quantified result from this engagement, derived from `results.primary_metric`. Used as the industry reference point in ROI justifications. Never invented — always from actual engagement data. |
| `success_threshold` | string | Conditions that predict similar results are achievable at a new client. One sentence describing the minimum data, team, and infrastructure prerequisites. |
| `gap_analysis_template` | string | Template string with a `{gap}` placeholder for the maturity gap in points. Used by the use case generator to write calibrated ROI basis statements. |

Example calibration fields from `win-001`:
```json
{
  "industry_benchmark": "14% fuel cost reduction on $2.1M annual fleet spend",
  "success_threshold": "Most applicable when a TMS is in place and the dispatch team can adopt route suggestions within 30 days of deployment.",
  "gap_analysis_template": "Maturity gap of {gap} points from engagement baseline — route optimisation ROI is achievable in 3–5 months with existing GPS telemetry and TMS API access."
}
```

---

## Maturity Labels

`maturity_at_engagement` uses the five-level scale from `docs/specs/analysis_spec.md`:

| Label | Score Range | Description |
|-------|-------------|-------------|
| Beginner | 1.0–1.9 | No systematic data infrastructure; manual processes only |
| Developing | 2.0–2.9 | Some data infrastructure; limited ML use; siloed |
| Emerging | 3.0–3.4 | Structured data pipelines; at least one production ML model |
| Advanced | 3.5–3.9 | Multiple production models; data platform in place |
| Leading | 4.0–5.0 | ML-native operations; active experimentation culture |

Distribution in this dataset:
- Beginner: 1 record (win-014)
- Developing: 16 records (majority)
- Emerging: 3 records (win-008, win-009, and one advanced case)

---

## Match Tiers

The RAG query agent assigns one of two match tiers when returning records:

| Tier | Criteria |
|------|----------|
| `DIRECT_MATCH` | Same industry, same use case type, maturity gap <= 1.5 points |
| `CALIBRATION_MATCH` | Adjacent industry or use case; maturity gap <= 2.5 points |

The use case generator uses `DIRECT_MATCH` records for `LOW_HANGING_FRUIT` tier
recommendations and `CALIBRATION_MATCH` records for `MEDIUM_SOLUTION` tier.

---

## Fixture Change Policy

Fixture files in `tests/fixtures/` are stable references — they do not change
mid-sprint. To update victory records:

1. File a new ticket: `[QA] update victories.json fixtures for sprint N+1`
2. Obtain PM approval
3. Re-run all tests that reference this file after the change

See CLAUDE.md Fixture data protection section for the full policy.

---

## Industries Covered

| Industry | Records |
|----------|---------|
| logistics | win-001, win-002, win-003 |
| financial_services | win-004, win-005, win-006 |
| healthcare | win-007, win-008, win-009 |
| retail | win-010, win-011 |
| manufacturing | win-012, win-013 |
| professional_services | win-014, win-015 |
| insurance | win-016, win-017 |
| energy | win-018 |
| real_estate | win-019 |
| construction | win-020 |
