# Loop State

> Updated after every agent returns. Read FIRST on /loop.

## Position
- **Cycle:** 2
- **Phase:** PROTOTYPE
- **Next action:** Add pain_point fixture signals, then test live extraction quality

## System Snapshot
- Signal types in schema: 10 (was 7 in cycle 1)
- Signal categories populated (dry-run): 7 of 8 (was 4 of 8 in cycle 1)
- Tools registered: website_scraper
- Agents in pipeline: scraper, signal_extractor, maturity_scorer, rag_query, use_case_generator, report_writer
- Test count: 124 passing, 0 regressions
- Eval scores: not measured this cycle

## Cycle 2: Schema Expansion

### What changed
1. **Schema expanded** (orchestrator/schemas.py): Signal.type now accepts 10 types.
   Added: process_signal, hiring_signal, pain_point.
2. **Fixture updated** (tests/fixtures/sample_signals.json): 12 signals (was 8).
   Added: sig-009 (process_signal: route optimization), sig-010 (process_signal: shipment tracking),
   sig-011 (hiring_signal: Senior Data Engineer), sig-012 (intent_signal: investing in intelligent tools).
3. **Prompt updated** (prompts/signal_extractor.md v1.1): extraction rules for all 3 new types,
   clarified intent_signal triggers (investment language).

### Category coverage after cycle 2

| Category           | Schema type      | Found? | Signals                                              |
|--------------------|------------------|--------|------------------------------------------------------|
| TECH_STACK         | tech_stack       | YES    | sig-001 (BigQuery), sig-002 (Airflow)                |
| DATA_ASSETS        | data_signal      | YES    | sig-003 (50M+ events), sig-008 (PostgreSQL/Redis)    |
| HIRING_SIGNALS     | hiring_signal    | YES    | sig-011 (Senior Data Engineer)                       |
| PROCESS_SIGNALS    | process_signal   | YES    | sig-009 (route optimization), sig-010 (shipment tracking) |
| SCALE_INDICATORS   | scale_hint       | YES    | sig-007 (mid-market)                                 |
| STRATEGY_SIGNALS   | intent_signal    | YES    | sig-012 (investing in intelligent logistics tools)   |
| PAIN_POINTS        | pain_point       | NO     | Type exists in schema but no fixture signals yet     |
| DELIVERED_MATCHES  | (via RAG/victory)| YES    | 3 victories matched (win-001, win-002, win-003)      |

**Found: 7 of 8. Missing: PAIN_POINTS (schema supports it, fixture has no examples).**

### Remaining gap: PAIN_POINTS
The pain_point type is now in the schema and the prompt has extraction rules, but the
CargoLogik fixture text doesn't contain explicit pain language ("manual process", "legacy
system", etc.). Two options:
1. Add pain_point signals to the fixture (the source text implies pain but doesn't state it)
2. Accept that not all companies will have visible pain points -- this is an honest gap

### Delta from cycle 1
| Metric                    | Cycle 1 | Cycle 2 | Change    |
|---------------------------|---------|---------|-----------|
| Schema signal types       | 7       | 10      | +3        |
| Fixture signal count      | 8       | 12      | +4        |
| Categories populated      | 4/8     | 7/8     | +3        |
| Tests passing             | 124     | 124     | no change |
| Regressions               | 0       | 0       | clean     |

## Cycle 1: Signal Catalogue Audit (archived)

Pipeline ran against CargoLogik fixture. 8 signals across 5 types. 4 of 8 consultant
categories populated. Diagnosis: 3 types structurally missing from schema, 1 type
(intent_signal) present but unextracted. See git history for full audit tables.

## Convergence
- [x] Pipeline completes for fixture company
- [ ] Exec summary: CFO-ready in 30 seconds
- [ ] Every claim traces to a signal
- [ ] Missing signals shown with confidence impact
- [x] Business processes named specifically (sig-009, sig-010)
- [ ] Delivered tier: victory win_id + ROI cited
- [ ] Developing tier: calibration basis shown
- [ ] Ambitious tier: real companies cited
- [ ] ROI math: complete chain
- [ ] Thin-signal: honest LOW confidence
- [ ] No agent context overflow
- [x] All tests pass

## Blockers for Sai
- (none -- previous blocker resolved: schema now supports 10 types)

## Handoff
Cycle 2 complete. Schema and prompt expanded. 7 of 8 categories populated.
Next: decide whether to add pain_point fixture data or move to report quality audit.
