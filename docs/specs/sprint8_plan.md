# Sprint 8 Plan: Delivered Solutions Redesign

Version: 1.0
Date: 2026-03-19
Owner: PM

---

## Sprint Goal

Redesign the delivered solutions library as a first-class system component with its own
ingestion pipeline, schema validation, and clearly demarcated matching interface -- so
the solution store grows cleanly and matching quality can be measured precisely.

---

## What Sai Can See and Test at Sprint End

| Deliverable | How to verify |
|-------------|---------------|
| New solution schema with all required fields | `python rag/validate_solution.py tests/fixtures/rag_seeds/victories.json` -- all records pass |
| Ingestion CLI for adding new solutions | `python rag/ingest_solution.py --file path/to/solution.json` -- record added, validated, embedded |
| Matching interface with explicit input/output contract | `python -c "from orchestrator.matching_layer import match; print(match.__doc__)"` |
| Eval: tier_classification above 3.80 | `python evals/ci_eval.py` -- averages show >= 3.80 for all 3 dimensions |
| Match quality eval rubric | `cat evals/rubrics/match_quality.yaml` |
| Dry-run pipeline still passes | `python orchestrator/pipeline.py --dry-run` |
| All existing tests pass | `pytest tests/ -q --tb=short` |

---

## Architecture: Two Pipelines, One Matching Layer

```
COMPANY ANALYSIS PIPELINE              DELIVERED SOLUTIONS LIBRARY
(about the TARGET company)             (about what TENEX HAS DONE)

  URL Input                              Solution JSON input
      |                                        |
  Stage 1: Scraper                       Validate schema
      |                                        |
  Stage 2: Signal Extractor              Generate embed_text
      |                                        |
  Stage 3: Maturity Scorer              Embed via ChromaDB
      |                                        |
  Stage 4: RAG Query  ---retrieval-----> ChromaDB Solutions Store
      |                    query               |
      v                                        v
                                        
  =================== MATCHING LAYER =========================
  
  Input A: SignalSet (industry, scale, maturity)    [from analysis pipeline]
  Input B: list[SolutionRecord]                     [from RAG retrieval]
  
  orchestrator/matching_layer.py
    match(signals: SignalSet, maturity: MaturityResult, rag_results: list[dict])
      -> list[VictoryMatch]
  
  Scoring dimensions (deterministic, no model call):
    - industry_score    (0-0.4): exact / related / unrelated
    - maturity_score    (0-0.4): same label / adjacent / distant
    - size_score        (0-0.2): same tier / adjacent / different
    - sector_tag_bonus  (0-0.1): any sector_tag overlap
  
  Tier thresholds:
    DIRECT_MATCH:      total >= 0.75 AND industry_score > 0
    CALIBRATION_MATCH: total >= 0.45
    ADJACENT_MATCH:    below 0.45
  
  ============================================================
      |
      v
  Stage 5: Victory Matcher (calls matching_layer.match())
      |
  Stage 6: Use Case Generator
      |
  Stage 7: Report Writer
      |
  API Response / UI
```

### Separation contract

The analysis pipeline produces: `SignalSet + MaturityResult`
The solutions library produces: `list[SolutionRecord]`
The matching layer receives BOTH and produces: `list[VictoryMatch]`

No analysis agent reads the solutions store directly.
No solution ingestion touches the analysis pipeline.
The matching layer is the only bridge.

---

## What Is Wrong Right Now (Gap Analysis)

### Current victories.json -- what exists

The 20 win records have solid core structure:
- `problem_statement`, `solution_summary`, `results`, `engagement_details`, `tech_stack`
- `industry_benchmark` and `gap_analysis_template` added in Sprint 7
- `embed_text` for ChromaDB ingestion

### What is missing from the data model

1. `ingestion_date` -- no audit trail for when a record was added
2. `status` field -- no way to mark records as draft / active / deprecated
3. `sector_tags` present but not used in matching logic -- unscored, zero weight
4. `solution_category` -- no classification of the type of AI applied
   (predictive_model | classification | nlp | computer_vision | optimization | scoring_model)
5. `applicable_signals` -- no explicit mapping from solution to signal types that would trigger it
   Currently matching is purely semantic (embed similarity + industry/maturity/size scoring)
   A solution record should declare which signal types make it relevant
6. No ingestion validation -- records are hand-edited JSON with no schema enforcement
7. No ingestion CLI -- adding a new solution means editing a fixture file and hoping

### What is wrong with the matching layer

1. `victory_matcher.py` is named but does two things: it IS the matching layer, and it
   computes gap analysis. These should be split.
2. `sector_tag_bonus` does not exist -- sector overlap is ignored in scoring
3. Tier thresholds: DIRECT_MATCH requires >= 0.7 but the max score is 1.0 and
   most wins score 0.6-0.8 for close matches. Threshold calibration is untested.
4. The matching interface is not a named, documented contract. It is an internal function.

### What is wrong with evals

1. `tier_classification` stuck at 3.67 across 3 cycles. The rubric asks for
   "appropriate tier supported by at least one cited evidence signal" to score 4.
   The fixture use cases cite signal IDs but the judge does not clearly see
   the connection between those signals and the tier assignment in the rationale.
2. No eval rubric for matching quality. We can measure use case quality but not
   whether the right solution was retrieved for a given company profile.
3. Eval scores fluctuate between runs (roi_basis: 3.67-3.80). The judge receives
   free-text signals_summary which introduces variance. Switching to structured
   signal citations reduces judge interpretation variance.

---

## Tickets

### Priority Order and Dependencies

```
DISC-66 (BE) - Delivered Solutions schema + validator     [p1, no deps]
DISC-67 (BE) - Ingestion CLI for adding new solutions     [p1, depends on DISC-66]
DISC-68 (BE) - Matching layer extraction + sector scoring [p1, depends on DISC-66]
DISC-69 (QA) - Match quality eval rubric                  [p1, depends on DISC-68]
DISC-70 (BE) - Fix tier_classification: use case rationale strengthening  [p1, no deps]
DISC-71 (PM) - Update solution spec and ADR-007           [p2, depends on DISC-66]
DISC-72 (QA) - Eval runner: add match_quality dimension   [p2, depends on DISC-69]
DISC-73 (FE) - Solution browser UI (read-only list view)  [p3, depends on DISC-66]
```

---

### DISC-66 [BE]: Delivered Solutions schema validator

**User story:** As a Tenex engineer, I need a schema validator for solution records
so that new solutions added to the store are complete and structurally correct before
they are embedded.

**done_when:** `rag/validate_solution.py` validates a dict against the solution schema,
returns a list of field errors (empty = valid), and all 20 existing victory records pass.

**Acceptance criteria:**
- `rag/validate_solution.py` defines `SolutionSchema` as a Pydantic model
- All required fields enforced: id, engagement_title, industry, company_profile,
  problem_statement, solution_summary, results, engagement_details, tech_stack,
  embed_text
- New required fields added: `status` (enum: draft/active/deprecated),
  `ingestion_date` (ISO date string), `solution_category` (enum: see below),
  `applicable_signals` (list of signal type strings)
- `solution_category` enum: predictive_model | classification | nlp | computer_vision |
  optimization | scoring_model
- `applicable_signals` maps to Signal.type values from orchestrator/schemas.py
- All 20 existing victories.json records pass validation after a one-time backfill
  (backfill script adds missing fields with sensible defaults)
- Validation errors are human-readable: "win-007: missing field 'ingestion_date'"
- `SolutionSchema` exported from `rag/validate_solution.py` -- importable by ingestion CLI

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: Python schema work in rag/ directory, BE ownership

**Test certification required:** yes
**Decision required:** yes (new schema fields extend ADR-007)
**Blocked by:** none

---

### DISC-67 [BE]: Ingestion CLI for delivered solutions

**User story:** As a Tenex engagement lead, I need a command-line tool to add a new
delivered solution to the store so that the library grows after each engagement without
manual JSON editing.

**done_when:** `python rag/ingest_solution.py --file solution.json` validates,
embeds, and upserts one or more solution records into ChromaDB, printing a clear
success or error summary. A test fixture solution passes end-to-end in dry-run mode.

**Acceptance criteria:**
- `rag/ingest_solution.py` accepts `--file <path>` and `--dry-run` flags
- Validates the input file against `SolutionSchema` before touching the store
- On validation failure, prints field errors and exits non-zero -- nothing is written
- On success, generates `embed_text` if absent, upserts to ChromaDB, prints confirmation
- `--dry-run` validates and logs what would be written but does not call ChromaDB
- Idempotent: running the same file twice does not duplicate the record (upsert by id)
- Exit codes: 0 = success, 1 = validation failure, 2 = store write failure
- `rag/ingest.py` `ensure_seeds_loaded()` updated to use the same validation path
  so existing ingest also validates before loading

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: Python CLI in rag/ directory, BE ownership

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-66

---

### DISC-68 [BE]: Matching layer extraction and sector scoring

**User story:** As a developer, I need the matching logic in a named, documented
module with a clear interface so that signals come in one side, solutions come in the
other, and the contract is testable.

**done_when:** `orchestrator/matching_layer.py` exports `match()` with a typed
signature, `victory_matcher.py` delegates to it, and sector tag overlap contributes
to scoring. All existing victory matcher tests pass.

**Acceptance criteria:**
- `orchestrator/matching_layer.py` contains `match(signals: SignalSet, maturity: MaturityResult, rag_results: list[dict]) -> list[VictoryMatch]`
- Function docstring documents the scoring dimensions and tier thresholds
- Scoring adds `sector_tag_bonus` (0.0-0.1): +0.05 per matching sector_tag, capped at 0.1
- `applicable_signals` from the solution record used as bonus: +0.05 if any signal type
  in the company SignalSet matches `applicable_signals` on the solution, capped at 0.1
- Total max score: 1.0 (industry 0.4 + maturity 0.4 + size 0.2 + sector 0.1 + signal 0.1,
  but capped so the tiers still work: 0.4+0.4+0.2 = 1.0 max before bonuses)
  Note: bonuses elevate borderline cases -- calibrate thresholds accordingly
- DIRECT_MATCH threshold updated to >= 0.75 (was 0.7, now more selective)
- CALIBRATION_MATCH threshold updated to >= 0.45 (was 0.4)
- `orchestrator/victory_matcher.py` is a thin wrapper that calls `matching_layer.match()`
  -- it no longer contains the scoring logic
- `_compute_gap_analysis()` stays in `victory_matcher.py` (it is output formatting, not matching)
- `tests/test_victory_matcher.py` updated to test via the new interface
- `tests/test_matching_layer.py` added with unit tests for each scoring dimension

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: Python refactor in orchestrator/ directory, BE ownership

**Test certification required:** yes
**Decision required:** yes (matching interface change is an architecture decision -- new ADR-011)
**Blocked by:** DISC-66

---

### DISC-69 [QA]: Match quality eval rubric

**User story:** As a product manager, I need an eval rubric that measures whether the
right delivered solutions were retrieved for a given company profile so that match quality
is measurable sprint over sprint.

**done_when:** `evals/rubrics/match_quality.yaml` defines a 1-5 rubric that a judge
can score deterministically given a company profile and a list of VictoryMatch records.

**Acceptance criteria:**
- `evals/rubrics/match_quality.yaml` follows the format of existing rubrics
- Rubric evaluates: does the top-ranked VictoryMatch share the company's industry?
  Does the tier assignment (DIRECT/CALIBRATION/ADJACENT) match the similarity score?
  Is there at least one DIRECT_MATCH or CALIBRATION_MATCH in the top 3 results?
- Score anchors:
  1 = Top result is wrong industry, no meaningful match
  2 = Industry match but maturity/size mismatch, tier assignment looks wrong
  3 = Plausible match but tier assignments are not well-calibrated to scores
  4 = Correct industry, appropriate tier, scores are internally consistent
  5 = Top match is same industry + same maturity tier, tier assignment is fully justified
- `judge_prompt_template` provides: company profile summary, top 3 VictoryMatch records
  with their similarity_score and match_tier, and the scoring rubric
- Rubric can be evaluated deterministically (no free-text interpretation needed for 3-5)

**Execute with:**
  Primary: qa
  Collaborators: none
  Reason: eval rubric in evals/rubrics/, QA ownership

**Test certification required:** no (rubric is a YAML spec, not executable code)
**Decision required:** no
**Blocked by:** DISC-68 (needs the new matching interface to know what fields are available)

---

### DISC-70 [BE]: Fix tier_classification eval score

**User story:** As the PM, I need tier_classification eval score to reach >= 3.80 so
that all three existing eval dimensions are above threshold before Sprint 8 closes.

**done_when:** Running `python evals/ci_eval.py` with the sprint_8 key produces
tier_classification average >= 3.80 across all test companies.

**Acceptance criteria:**
- Root cause identified: current fixture use cases cite signal IDs but the judge does
  not see a clear rationale connecting signals to the tier assignment
- Fix applied to `tests/fixtures/sample_analysis.json` use cases: each LOW_HANGING_FRUIT
  use case adds an explicit rationale in `why_this_company` that names the tier, references
  the maturity score range, and cites at least 2 signal IDs with their values
- `tests/fixtures/sample_use_cases.json` (if separate) updated to match
- No prompt changes required unless fixture fix is insufficient -- if prompt change is
  needed, update `prompts/use_case_generator.md` to v1.2 and log in `prompts/VERSIONS.md`
- `evals/ci_eval.py` updated to `_SPRINT = "sprint_8"` with a new entry in baselines.json
- tier_classification average >= 3.80 verified (do not close without actual score)
- All three dimensions: tier_classification >= 3.80, evidence_grounding >= 3.80,
  roi_basis >= 3.80

**Execute with:**
  Primary: backend
  Collaborators: none
  Reason: fixture and prompt files, BE owns fixtures; PM owns prompts if needed

**Test certification required:** yes
**Decision required:** no
**Blocked by:** none (independent of schema changes)

---

### DISC-71 [PM]: Update solution spec and record ADR-011

**User story:** As a developer joining the project, I need the solution data spec and
decision records to reflect the new schema so that new solutions can be added without
asking anyone.

**done_when:** `docs/specs/victory_data_spec.md` updated with new fields, ADR-011
recorded for the matching layer contract, INDEX.md updated.

**Acceptance criteria:**
- `docs/specs/victory_data_spec.md` updated to v2.0:
  - New required fields documented: status, ingestion_date, solution_category, applicable_signals
  - Ingestion CLI usage documented with example command
  - Validation rules for new fields documented
- `docs/decisions/ADR-011.md` created: "Matching Layer Interface Contract"
  - Documents the `match()` function signature
  - Documents the two-pipeline architecture with matching layer as bridge
  - Documents scoring dimensions and tier thresholds
- `docs/decisions/INDEX.md` updated with ADR-011 entry
- `docs/ARCHITECTURE.md` updated to show two-pipeline diagram from this sprint plan

**Execute with:**
  Primary: pm
  Collaborators: none
  Reason: docs/specs and docs/decisions are PM ownership

**Test certification required:** no
**Decision required:** no (this ticket IS the decision documentation)
**Blocked by:** DISC-68 (needs final matching interface to document accurately)

---

### DISC-72 [QA]: Eval runner: add match_quality dimension

**User story:** As the PM, I need the eval runner to score match_quality each sprint
so that retrieval quality is tracked sprint over sprint alongside use case quality.

**done_when:** `evals/ci_eval.py` scores match_quality per test company using the new
rubric and includes it in baselines.json output alongside the existing three dimensions.

**Acceptance criteria:**
- `_RUBRICS` dict in `ci_eval.py` extended with `"match_quality": <path to rubric>`
- `_uc_vars()` or a new `_match_vars()` function constructs the judge context:
  company name, top 3 VictoryMatch records (win_id, match_tier, similarity_score,
  industry, roi_benchmark), company industry and maturity_label
- Sprint_8 baseline includes `match_quality` scores per company and in averages
- match_quality baseline target: >= 3.5 (new dimension, lower threshold on first sprint)
- Existing three dimensions still scored and reported

**Execute with:**
  Primary: qa
  Collaborators: none
  Reason: evals/ directory is QA ownership

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-69 (needs the rubric), DISC-68 (needs match output to feed into judge context)

---

### DISC-73 [FE]: Solution browser UI (read-only list view)

**User story:** As Sai during a demo, I need to see the delivered solutions library
in the UI so that I can show a client "these are the solutions we've delivered" alongside
the analysis.

**done_when:** Navigating to `/solutions` in the frontend shows a list of all solutions
from the store with industry, engagement title, primary metric, and match tier displayed
for each card.

**Acceptance criteria:**
- `/solutions` page added using Next.js App Router
- GET `/v1/solutions` backend endpoint returns all active solution records (status=active)
  as JSON -- BE must implement this endpoint (collaborator task)
- Each solution displays: engagement_title, industry, company_profile.size_label,
  primary_metric label and value, solution_category tag
- Loading state: skeleton cards while fetching
- Error state: "Could not load solutions" message if fetch fails
- Page is reachable from main nav (link added to header)
- No authentication required (consistent with ADR-002)
- Mobile-responsive (cards stack vertically on small screens)

**Execute with:**
  Primary: frontend
  Collaborators: backend (needs GET /v1/solutions endpoint)
  Reason: TypeScript/React page in frontend/, FE ownership; BE adds one API endpoint

**Test certification required:** yes
**Decision required:** no
**Blocked by:** DISC-66 (needs solution records to have stable structure), DISC-67 (needs active status field)

---

## Priority Order

| Ticket | Priority | Reason |
|--------|----------|--------|
| DISC-66 | p1 | Foundation -- all other backend tickets depend on the schema |
| DISC-70 | p1 | Eval debt -- tier_classification at 3.67 blocks sprint close |
| DISC-67 | p1 | Enables live ingestion -- core of Sai's directive |
| DISC-68 | p1 | Matching layer is the architectural pivot Sai requested |
| DISC-69 | p1 | Match quality must be measurable before sprint closes |
| DISC-71 | p2 | Documentation follows implementation |
| DISC-72 | p2 | Eval extension -- useful but not blocking demo |
| DISC-73 | p3 | Nice-to-have UI -- can slip if BE work takes longer |

---

## Execution Sequence

```
Week 1:
  Day 1-2: DISC-66 (BE) -- schema + validator + backfill of 20 records
  Day 2-3: DISC-70 (BE) -- fix tier_classification (independent, fast)
  Day 3-4: DISC-67 (BE) -- ingestion CLI (depends on DISC-66)

Week 2:
  Day 5-6: DISC-68 (BE) -- matching layer extraction (depends on DISC-66)
  Day 6-7: DISC-69 (QA) -- match quality rubric (depends on DISC-68)
  Day 7:   DISC-71 (PM) -- update docs (depends on DISC-68)
  Day 7-8: DISC-72 (QA) -- eval runner update (depends on DISC-69 + DISC-68)
  Day 8-9: DISC-73 (FE) -- solution browser (depends on DISC-66 + DISC-67)
```

Note: DISC-73 (FE) requires a BE collaborator to add GET /v1/solutions.
That endpoint should be added as part of DISC-67 or as a sub-task.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Backfilling 20 victory records with new fields takes longer than estimated | Medium | Low | Backfill can use sensible defaults for `applicable_signals` -- refine in Sprint 9 |
| Matching layer threshold recalibration breaks existing tests | Medium | Medium | Test thresholds against all 20 wins before merging; keep old thresholds as config |
| tier_classification still below 3.80 after fixture fix | Low | Medium | If fixture is insufficient, prompt change to use_case_generator.md as fallback |
| DISC-73 (FE) slips due to BE endpoint dependency | Medium | Low | p3 priority -- can slip to Sprint 9; rest of sprint goal holds without it |
| Eval variance persists even with structured context | Low | Medium | Add deterministic scoring dimensions to reduce LLM judge surface area |

---

## Sprint 8 Success Criteria

At sprint close, Sai can:

1. Run `python rag/ingest_solution.py --file tests/fixtures/sample_solution.json --dry-run`
   and see validation pass and embed_text logged.

2. Run `python orchestrator/pipeline.py --dry-run` and see the matching layer produce
   VictoryMatch records with sector_tag_bonus and applicable_signals scoring visible in logs.

3. Run `python evals/ci_eval.py` and see all 4 dimensions >= threshold:
   - tier_classification >= 3.80
   - evidence_grounding >= 3.80
   - roi_basis >= 3.80
   - match_quality >= 3.50

4. Browse to `/solutions` in the UI and see the 20 delivered solutions as cards.

5. The two-pipeline architecture is documented in `docs/ARCHITECTURE.md` with a diagram.
