# Loop State

> Updated after every agent returns. Read FIRST on /loop.

## Position
- **Cycle:** 4
- **Phase:** EXECUTION (Sprint 8, Phase 5 -- Eval + Docs)
- **Next action:** DISC-72 (QA eval runner) and DISC-73 (FE solution browser) remaining

## Sprint 8 Plan Revision Note

Sprint 8 plan revised per Sai's 3-tier matching directive (2026-03-19).

Original plan (v1.0): single matching layer, one library, tier thresholds only.
Revised plan (v2.0): two separate libraries, three output tracks, independent synthesis.

Key changes from v1.0:
- Library A (Tenex wins) and Library B (industry cases) are separate ChromaDB collections
- Matching layer outputs three distinct tracks: DELIVERED, ADAPTATION, AMBITIOUS
- Each track has its own synthesis prompt, confidence band, and evidence requirements
- DELIVERED = direct win match (confidence >= 0.80), cite exact proven metrics
- ADAPTATION = adjacent win match (confidence 0.55-0.79), explain the gap and delta
- AMBITIOUS = industry evidence match (confidence 0.40-0.65), cite external companies
- UI shows three labeled sections, not just tier badges on individual cards
- Two new tickets added: DISC-74 (industry ingestion CLI), DISC-75 (tier prompts)
- DISC-76 replaces partial use case generator work with full per-tier synthesis

## System Snapshot
- Signal types in schema: 10
- Signal categories populated (dry-run): 7 of 8 (pain_point absent by design)
- Eval scores (sprint_7): tier=3.67, evidence=4.67, roi=3.80
- Test count: 124 passing, 0 regressions
- Prompt versions: signal_extractor v1.1, maturity_scorer v1.1, use_case_generator v1.1
- Solution records in library: 20 (victories.json -- Library A)
- Industry case records: 0 (Library B not yet populated -- DISC-74)

## Cycle 4: Three-Tier Matching Architecture

### Sai's Directive (Sprint 8 pivot, revised)
1. Delivered solutions library is the core value prop -- redesign as first-class.
2. Two separate libraries: Tenex wins (Library A) and industry cases (Library B).
3. Three output tracks: DELIVERED (proven), ADAPTATION (adjacent), AMBITIOUS (market intel).
4. Each tier has its own data source, synthesis prompt, confidence band, and UI panel.
5. No cross-contamination: Library A only feeds DELIVERED and ADAPTATION.
   Library B only feeds AMBITIOUS.
6. Evals must cover match quality per tier.

### Sprint 8 Tickets (revised from v1.0)

| Ticket | Owner | Title | Priority | Depends On |
|--------|-------|-------|----------|------------|
| DISC-66 | BE | Schema definitions: SolutionRecord, IndustryCaseStudy, MatchResult | p1 | none |
| DISC-67 | BE | Delivered solutions ingestion CLI (Library A) | p1 | DISC-66 |
| DISC-74 | BE | Industry cases ingestion CLI (Library B) | p1 | DISC-66 |
| DISC-68 | BE | Matching layer: 3-channel logic, two ChromaDB collections | p1 | DISC-66 |
| DISC-70 | BE | Fix tier_classification eval score to >= 3.80 | p1 | none |
| DISC-75 | PM | Three synthesis prompts (one per tier) | p1 | none |
| DISC-76 | BE | Use case generator: per-tier synthesis using tier prompts | p2 | DISC-68, DISC-75 |
| DISC-77 | FE | UI: three-tier panels (Delivered, Adaptation, Ambitious) | p2 | DISC-68 |
| DISC-69 | QA | Match quality eval rubric (per-tier version) | p2 | DISC-68 |
| DISC-71 | PM | ADR-011 for 3-tier architecture + spec updates | p2 | DISC-68 |
| DISC-72 | QA | Eval runner: match_quality per tier | p3 | DISC-69, DISC-68 |
| DISC-73 | FE | Solution browser: Library A list view | p3 | DISC-67 |

### Architecture pivot (v2.0)
Two libraries, one matching layer, three output tracks.
`orchestrator/matching_layer.py` is the bridge -- no agent reads either library directly.
`rag/ingest_solution.py` -- Library A ingestion (Tenex wins).
`rag/ingest_industry_case.py` -- Library B ingestion (industry cases).
ChromaDB collections: "tenex_delivered" and "industry_cases" (separate from old "ai_solutions").
`orchestrator/schemas.py` gains `MatchResult` replacing `VictoryMatch` (alias kept for compat).

### Eval targets (Sprint 8)
- tier_classification >= 3.80 (currently 3.67 -- DISC-70)
- evidence_grounding >= 3.80 (currently 4.67 -- hold)
- roi_basis >= 3.80 (currently 3.80 -- hold)
- match_quality_delivered >= 3.50 (new -- DISC-72)
- match_quality_adaptation >= 3.00 (new -- DISC-72)
- match_quality_ambitious >= 2.80 (new -- DISC-72)

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
- [x] Adaptation tier: base win + gap analysis + adapted ROI (DISC-68 done)
- [x] Ambitious tier: industry cases in Library B (DISC-74 done)
- [x] ROI math: complete chain (win benchmark + gap analysis + quantified estimate)
- [ ] Thin-signal: honest LOW confidence
- [ ] No agent context overflow
- [x] All tests pass
- [x] Delivered solutions: own ingestion pipeline -- Library A (DISC-67 done)
- [x] Industry cases: own ingestion pipeline -- Library B (DISC-74 done)
- [x] Matching layer: three-channel, named contract (DISC-68 done)
- [x] Synthesis: per-tier prompts written (DISC-75 done)
- [ ] Match quality: measurable via eval per tier (DISC-69, DISC-72)
- [ ] Three-tier UI: Delivered/Adaptation/Ambitious panels (DISC-77)

## Blockers for Sai
- (none)

## Handoff
Cycle 4, Sprint 8 plan revised to v2.0 per Sai's 3-tier directive.
Full plan at docs/specs/sprint8_plan.md.
Execute DISC-66 first (BE) -- foundation for all other tickets.
DISC-70 (eval fix) and DISC-75 (tier prompts) can run in parallel with DISC-66.
