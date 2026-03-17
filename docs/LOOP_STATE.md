# Loop State

> Updated after every agent returns. Read FIRST on /loop.

## Position
- **Cycle:** 1
- **Phase:** PROTOTYPE
- **Next action:** Fix signal catalogue gaps identified below

## System Snapshot
- Signal categories extracted: 5 of 7 prompt-defined types
- Tools registered: website_scraper
- Agents in pipeline: scraper, signal_extractor, maturity_scorer, rag_query, use_case_generator, report_writer
- Test count: not measured this cycle
- Eval scores: not measured this cycle

## Signal Catalogue Audit (Cycle 1)

### Step 1: Signals extracted from dry-run

Pipeline ran successfully against fixture company CargoLogik (mid-market B2B logistics SaaS).
8 signals extracted:

| signal_id | type           | value                        | source      | raw_quote                                          | confidence |
|-----------|----------------|------------------------------|-------------|-----------------------------------------------------|------------|
| sig-001   | tech_stack     | BigQuery                     | about_text  | BigQuery data lake with Airflow orchestration       | 0.95       |
| sig-002   | tech_stack     | Airflow                      | about_text  | BigQuery data lake with Airflow orchestration       | 0.95       |
| sig-003   | data_signal    | 50M+ events daily            | job_posting | processing 50M+ events daily                       | 0.90       |
| sig-004   | ml_signal      | No ML/AI roles in postings   | job_posting | Data Engineer, Product Manager, Full Stack Engineer | 0.80       |
| sig-005   | ops_signal     | Kubernetes                   | job_posting | Kubernetes, Docker, CI/CD                           | 0.90       |
| sig-006   | industry_hint  | logistics                    | about_text  | 2M+ shipments monthly across 200+ logistics custo  | 0.95       |
| sig-007   | scale_hint     | mid-market                   | about_text  | 200+ customers                                     | 0.85       |
| sig-008   | data_signal    | PostgreSQL and Redis stack   | job_posting | PostgreSQL, Redis                                   | 0.90       |

### Step 2: Gap analysis against 8-category consultant catalogue

| Category           | Schema type      | Found? | Signals                          |
|--------------------|------------------|--------|----------------------------------|
| TECH_STACK         | tech_stack       | YES    | sig-001 (BigQuery), sig-002 (Airflow) |
| DATA_ASSETS        | data_signal      | YES    | sig-003 (50M+ events), sig-008 (PostgreSQL/Redis)  |
| HIRING_SIGNALS     | (none)           | NO     | No type exists in schema         |
| PROCESS_SIGNALS    | (none)           | NO     | No type exists in schema         |
| SCALE_INDICATORS   | scale_hint       | YES    | sig-007 (mid-market)             |
| STRATEGY_SIGNALS   | intent_signal    | NO     | Type exists in schema but no signals extracted      |
| PAIN_POINTS        | (none)           | NO     | No type exists in schema         |
| DELIVERED_MATCHES  | (via RAG/victory)| YES    | 3 victories matched (win-001, win-002, win-003)     |

**Found: 4 of 8 categories. Missing: HIRING_SIGNALS, PROCESS_SIGNALS, STRATEGY_SIGNALS, PAIN_POINTS.**

Three of those four are structurally missing: the Signal schema (schemas.py line 11-14)
only defines 7 types: tech_stack, data_signal, ml_signal, intent_signal, ops_signal,
industry_hint, scale_hint. There is no type for hiring signals, process signals, or
pain points. These categories cannot be extracted because the schema rejects them.

The fourth (STRATEGY_SIGNALS / intent_signal) exists in the schema but the fixture
produced zero signals of this type. The source data does contain "investing in data
infrastructure to support our next generation of intelligent logistics tools" which
should produce an intent_signal but the fixture omits it.

### Step 3: Signal quality evaluation

| signal_id | raw_quote present? | Value specific or generic? | Consultant usable? | Notes                                      |
|-----------|--------------------|----------------------------|--------------------|---------------------------------------------|
| sig-001   | Yes                | Specific (BigQuery)        | Yes                | Named tool, clear evidence                  |
| sig-002   | Yes                | Specific (Airflow)         | Yes                | Named tool, clear evidence                  |
| sig-003   | Yes                | Specific (50M+ events)     | Yes                | Quantified volume, strong signal            |
| sig-004   | Yes                | Specific (absence signal)  | Moderate           | Absence of ML roles is useful but negative signals are harder to act on |
| sig-005   | Yes                | Specific (Kubernetes)      | Yes                | Named infra tool                            |
| sig-006   | Yes                | Specific (logistics)       | Yes                | Clear industry tag                          |
| sig-007   | Yes                | Generic (mid-market)       | Moderate           | Label only, no quantified revenue/headcount |
| sig-008   | Yes                | Specific (PostgreSQL/Redis)| Yes                | Named tools                                |

All 8 signals have non-empty raw_quote fields. 6 of 8 are specific and consultant-usable.
sig-004 (absence signal) and sig-007 (generic label) are weaker.

### Step 4: Diagnosis -- single biggest gap

**The single biggest gap is the missing PROCESS_SIGNALS category.**

Why this matters most:
- A consultant's highest-value output is identifying which specific business processes
  are ripe for automation. The current pipeline extracts tools and data volume but never
  names a single business process. The fixture source text contains clear process signals:
  "route optimization", "warehouse management", "shipment tracking", "carrier performance
  monitoring", "fleet optimization" -- none of these are captured as typed signals.
- Without process signals, use case recommendations are grounded in tech stack presence
  rather than business pain. This makes the report read like a tech audit rather than a
  transformation strategy.
- HIRING_SIGNALS and PAIN_POINTS are also missing but are secondary: hiring signals
  overlap partially with ml_signal (absence of ML roles), and pain points require
  inference the extractor prompt currently forbids.

**What to change:**
1. Add 3 new signal types to the Signal schema (schemas.py): `hiring_signal`,
   `process_signal`, `pain_point`
2. Update the signal extractor prompt (prompts/signal_extractor.md) to define and
   request these types with extraction rules
3. Update the fixture (tests/fixtures/sample_signals.json) to include examples of
   the new types extracted from CargoLogik source text
4. Consider adding `intent_signal` examples to the fixture since the source text
   supports it but the fixture omits it

## Convergence
- [x] Pipeline completes for fixture company
- [ ] Exec summary: CFO-ready in 30 seconds
- [ ] Every claim traces to a signal
- [ ] Missing signals shown with confidence impact
- [ ] Business processes named specifically
- [ ] Delivered tier: victory win_id + ROI cited
- [ ] Developing tier: calibration basis shown
- [ ] Ambitious tier: real companies cited
- [ ] ROI math: complete chain
- [ ] Thin-signal: honest LOW confidence
- [ ] No agent context overflow
- [ ] All tests pass

## Blockers for Sai
- Schema only supports 7 signal types; 3 consultant-critical categories have no type

## Handoff
Audit complete. Next step: expand Signal schema and prompt to cover all 8 categories.
