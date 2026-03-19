# Loop State

> Updated after every agent returns. Read FIRST on /loop.

## Position
- **Cycle:** 4
- **Phase:** SPRINT PLANNING
- **Next action:** Execute sprint 8 tickets starting with DISC-66

## System Snapshot
- Signal types in schema: 10
- Signal categories populated (dry-run): 7 of 8 (pain_point absent by design)
- Eval scores (sprint_7): tier=3.67, evidence=4.67, roi=3.80
- Test count: 124 passing, 0 regressions
- Prompt versions: signal_extractor v1.1, maturity_scorer v1.1, use_case_generator v1.1
- Solution records in library: 20 (victories.json)

## Cycle 4: Delivered Solutions Redesign

### Sai's Directive (Sprint 8 pivot)
1. Delivered solutions library is the core value prop -- redesign it as first-class.
2. Clear separation between analysis pipeline (about target company) and solutions
   library (about what Tenex has done). Matching layer sits between them.
3. Solutions have their own ingestion pipeline -- not ad-hoc JSON editing.
4. Matching must be strong -- signals map clearly to solutions.
5. Evals must be tighter -- tier_classification at 3.67 still below 3.80 threshold.

### Sprint 8 Tickets

| Ticket | Owner | Title | Priority | Depends On |
|--------|-------|-------|----------|------------|
| DISC-66 | BE | Delivered Solutions schema validator | p1 | none |
| DISC-67 | BE | Ingestion CLI for delivered solutions | p1 | DISC-66 |
| DISC-68 | BE | Matching layer extraction + sector scoring | p1 | DISC-66 |
| DISC-69 | QA | Match quality eval rubric | p1 | DISC-68 |
| DISC-70 | BE | Fix tier_classification eval score | p1 | none |
| DISC-71 | PM | Update solution spec and ADR-011 | p2 | DISC-68 |
| DISC-72 | QA | Eval runner: add match_quality dimension | p2 | DISC-69 + DISC-68 |
| DISC-73 | FE | Solution browser UI (read-only list view) | p3 | DISC-66 + DISC-67 |

### Architecture pivot
The old `victory_matcher.py` becomes a thin wrapper.
`orchestrator/matching_layer.py` is the new named, documented bridge.
`rag/validate_solution.py` + `rag/ingest_solution.py` are the new ingestion path.

### Key schema additions (DISC-66)
- `status`: draft | active | deprecated
- `ingestion_date`: ISO date string
- `solution_category`: predictive_model | classification | nlp | computer_vision | optimization | scoring_model
- `applicable_signals`: list of Signal.type values

### Eval targets (Sprint 8)
- tier_classification >= 3.80 (currently 3.67 -- DISC-70)
- evidence_grounding >= 3.80 (currently 4.67 -- hold)
- roi_basis >= 3.80 (currently 3.80 -- hold)
- match_quality >= 3.50 (new dimension -- DISC-72)

## Cycle 3 Summary

### Sprint 7 eval scores (final)

| Dimension           | Sprint 6 | Sprint 7 | Delta  | Target | Status         |
|---------------------|----------|----------|--------|--------|----------------|
| tier_classification | 3.67     | 3.67     | +0.00  | >= 3.8 | BELOW TARGET   |
| evidence_grounding  | 3.20     | 4.67     | +1.47  | >= 3.8 | PASSED         |
| roi_basis           | 3.07     | 3.80     | +0.73  | >= 3.8 | PASSED (exact) |

2 of 3 dimensions pass. tier_classification carries into Sprint 8 as DISC-70.

## Convergence
- [x] Pipeline completes for fixture company
- [ ] Exec summary: CFO-ready in 30 seconds
- [ ] Every claim traces to a signal
- [ ] Missing signals shown with confidence impact
- [x] Business processes named specifically (sig-009, sig-010)
- [x] Delivered tier: victory win_id + ROI cited (roi_basis now includes gap analysis)
- [x] Developing tier: calibration basis shown
- [ ] Ambitious tier: real companies cited
- [x] ROI math: complete chain (win benchmark + gap analysis + quantified estimate)
- [ ] Thin-signal: honest LOW confidence
- [ ] No agent context overflow
- [x] All tests pass
- [ ] Delivered solutions: own ingestion pipeline (DISC-67)
- [ ] Matching layer: named, documented contract (DISC-68)
- [ ] Match quality: measurable via eval (DISC-69 + DISC-72)
- [ ] Solution browser: visible in UI (DISC-73)

## Blockers for Sai
- (none)

## Handoff
Cycle 4 started. Sprint 8 plan written to docs/specs/sprint8_plan.md.
Execute DISC-66 first (BE) -- it is the foundation for DISC-67 and DISC-68.
DISC-70 (tier_classification fix) can run in parallel -- no dependencies.
