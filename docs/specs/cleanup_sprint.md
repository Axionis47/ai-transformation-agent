# Dead Code Audit Results

> Produced from a full codebase scan on 2026-03-19.
> Branch: fe/DISC-65-nav-page-structure (scanned on working tree).
> All grep evidence is against the project root, excluding .venv and __pycache__.

---

## Files to Delete (orphaned or exact duplicates)

### 1. `agents/consultant.py`

Evidence: zero callers in production code.
- CLAUDE.md explicitly marks it: "dead, not imported by any agent (delete candidate)"
- The only file importing it is `tests/test_consultant.py` (its own test)
- Not referenced in `orchestrator/pipeline.py`, `app.py`, or any other Python module
- Superseded by the split agents: `signal_extractor.py`, `maturity_scorer.py`, `use_case_generator.py`

### 2. `tests/test_consultant.py`

Evidence: tests an orphaned module.
- Only tests `agents/consultant.py` which is itself dead
- Deleting both together removes ~270 lines with zero production coverage loss

### 3. `tests/test_pipeline_hardening 2.py` (space in filename)

Evidence: exact byte-for-byte duplicate of `tests/test_pipeline_hardening.py`.
- `diff` confirms identical contents
- Space in filename makes it unreachable by pytest glob patterns
- Not in git index (untracked per `git status`)

### 4. `ops/logger 2.py` (space in filename)

Evidence: exact duplicate of an older logger version, now outdated.
- `diff` shows it is missing `_truncate`, `_truncate_summary`, `log_agent_call` -- all of which `ops/logger.py` has
- Not in git index (untracked per `git status`)
- Nothing imports it (space in name prevents imports)

### 5. `frontend/app/page 2.tsx` (space in filename)

Evidence: older, simpler version of `frontend/app/page.tsx`.
- Both define `HomePage` component; `page.tsx` is the current version with proper hero section
- Not in git index (untracked per `git status`)
- Cannot be imported by Next.js routing (space in filename)

### 6. `frontend/next.config 2.mjs` (space in filename)

Evidence: older version of `frontend/next.config.mjs`.
- `diff` shows it is missing `output: 'standalone'` which is required for Docker/Cloud Run
- Not in git index (untracked per `git status`)
- Next.js uses `next.config.mjs`, not this file

### 7. `prompts/consultant.md`

Evidence: no active agent loads it.
- CLAUDE.md explicitly marks it: "dead, not imported by any agent (delete candidate)"
- The only Python code that references it is `agents/consultant.py` (also dead)
- `.claude/agents/prompt-eng.md` references it, but that is a meta-config file, not a pipeline file

---

## Unused Imports per File

### `orchestrator/pipeline.py`

- `BaseAgent` imported from `agents.base` but only used in the type annotation of `_run_with_timeout`. This is legitimate (used as type hint) -- not a removal candidate.
- `victory_output` imported from `orchestrator.stage_io` but never called in `pipeline.py`. The import line is `victory_input, victory_output,` but grepping `pipeline.py` shows `victory_output` appears only on that import line.

### `orchestrator/stage_io.py`

- `report_writer_input` function defined at line 105 but never imported by `pipeline.py`. The pipeline imports `report_writer_output` but not `report_writer_input`. Dead internal function.

### `agents/use_case_generator.py`

- `_TIER_ORDER` defined at line 19, never used inside the file or anywhere else in production code.
- `_TIER_TO_KEY` defined at line 20, never used inside the file or anywhere else in production code.

---

## Unreferenced Functions/Classes

### `orchestrator/stage_io.py::report_writer_input()`

- Defined at line 105. Zero grep matches outside the file itself.
- `pipeline.py` imports `report_writer_output` but not `report_writer_input`.
- Safe to delete.

### `orchestrator/victory_matcher.py::_compute_gap_analysis()`

- Called internally within `match_victories()` which is called by `pipeline.py`.
- Not orphaned. Keep.

### `agents/consultant.py::format_wins()`

- Only called by `ConsultantAgent._load_prompt()` in the same dead file.
- Removed when `agents/consultant.py` is deleted.

### `rag/backfill_solutions.py::backfill()` and `main()`

- `backfill_solutions.py` is a one-time migration script for Sprint 8 field backfill.
- Zero imports outside the file itself.
- Zero test coverage.
- The data migration it performs (adding `status`, `ingestion_date`, etc.) has already been applied to `victories.json`.
- Status: orphaned after its one-time run. Candidate for deletion or archiving.

---

## Duplicate Components

### `agents/use_case_generator.py` -- `_TIER_ORDER` and `_TIER_TO_KEY` constants

- `_TIER_ORDER` is defined in both `agents/use_case_generator.py` (line 19) and `tests/test_use_case_generator.py` (line 11).
- Neither definition is imported by the other.
- The agent-side copy is never referenced by agent logic -- it is unreachable dead code.
- The test-side copy drives the test assertion -- it is the only active one.

### `orchestrator/victory_matcher.py` -- `_proximity_score` and `_industries_related`

- `_proximity_score` is defined identically in both `orchestrator/victory_matcher.py` and `orchestrator/matching_layer.py`.
- `_industries_related` is defined in both files with slightly different logic (the matching_layer version handles compound labels better).
- `victory_matcher.py` is now a thin backwards-compat wrapper -- its internal `_proximity_score` and `_industries_related` are only used by `match_victories()`, which is itself only called as a fallback in `pipeline.py` line 205.
- These duplicates are coupled to `match_victories()` which is kept for backwards compat. Not safe to remove yet -- tied to Ticket BE: remove compat path.

---

## Orphaned Test Files

### `tests/test_consultant.py`

- Tests `agents/consultant.py` which is a dead module.
- All 13 tests pass only because the module still exists on disk.
- Should be deleted together with `agents/consultant.py`.

### `tests/test_pipeline_hardening 2.py`

- Exact duplicate with a space in the filename.
- Never collected by pytest (pytest glob does not match filenames with spaces by default).
- Delete immediately.

---

## Orphaned Fixtures

### `tests/fixtures/rag_seeds/seeds.json`

- Used only as a fallback in `rag/ingest.py` (line 49-53) and `rag/vector_store.py` (line 95) when `victories.json` is absent.
- `victories.json` exists with 20 records and is the primary source.
- The fallback path exists but `seeds.json` is a legacy file from Sprint 4.
- Status: low-value legacy fallback. Mark for removal in a follow-up sprint after confirming the fallback path is no longer needed.

No other fixture files are orphaned. All remaining fixtures (`sample_company.json`, `sample_analysis.json`, `sample_report.json`, `sample_maturity.json`, `sample_signals.json`, `sample_solution.json`, `sample_use_cases.json`, `sample_industry_case.json`, `industry_cases.json`, `victories.json`) are referenced by active agent dry-run paths or test files.

---

## Orphaned Prompts

### `prompts/consultant.md`

- CLAUDE.md marks it as "dead, not imported by any agent (delete candidate)".
- The only Python that reads it is `agents/consultant.py` (dead).
- Safe to delete after `agents/consultant.py` is removed.

All other prompts are active:
- `prompts/signal_extractor.md` -- loaded by `SignalExtractorAgent`
- `prompts/maturity_scorer.md` -- loaded by `MaturityScorerAgent`
- `prompts/use_case_generator.md` -- loaded by `UseCaseGeneratorAgent`
- `prompts/report_writer.md` -- loaded by `ReportWriterAgent`
- `prompts/tier1_delivered.md` -- loaded by `UseCaseGeneratorAgent._load_tier_prompt("delivered")`
- `prompts/tier2_adaptation.md` -- loaded by `UseCaseGeneratorAgent._load_tier_prompt("adaptation")`
- `prompts/tier3_ambitious.md` -- loaded by `UseCaseGeneratorAgent._load_tier_prompt("ambitious")`

---

## Stale Documentation

### `docs/SYSTEM_STATE.md` -- wrong startup command

- Line 46 says: `uvicorn infra.app:app --reload --port 8000`
- `infra/app.py` does not exist. The FastAPI app lives in `app.py` at the repo root.
- Correct command: `uvicorn app:app --reload --port 8000`
- The Dockerfile correctly uses `app:app`.
- This will confuse Sai when he tries to start the backend.

### `docs/SYSTEM_STATE.md` -- Sprint 6 files list references `infra/app.py`

- Line 177: `infra/app.py  <- AnalyzeSuccess model extended with pages_fetched, signal_count`
- This file does not exist. `AnalyzeSuccess` is defined in `app.py` at the root.

---

## Additional Notes

### `rag/backfill_solutions.py` -- one-time migration script

- This was a Sprint 8 migration tool to add Sprint 8 fields to `victories.json`.
- The migration has been applied. The file has no imports from the active pipeline.
- It can safely be deleted or moved to a `scripts/` directory if historical record is wanted.

### `agents/frontend/` directory -- partially deleted

- `git status` at session start showed `D agents/frontend/AGENT.md` and `D agents/frontend/skills/page_layout.md` as staged deletions.
- However, both files still exist on disk.
- The `.claude/agents/frontend.md` agent config points to `agents/frontend/AGENT.md` for agent instructions.
- This is a git stage conflict -- the files should either be committed as deleted or unstaged.
- The CLAUDE.md specifies agent configs live in `team/<role>/` not `agents/<role>/`.
- The actual working team config is in `team/frontend/`.

---

## Sprint Plan: Cleanup

### Ticket CL-1 -- Delete orphaned Python files and prompt

**Owner:** be
**Priority:** p1
**Files to delete:**
- `agents/consultant.py`
- `tests/test_consultant.py`
- `prompts/consultant.md`

**Done when:** All three files are removed from the repo, `pytest tests/ -q --tb=short` passes with no test referencing `ConsultantAgent`, and no CI breakage.

---

### Ticket CL-2 -- Delete duplicate/orphaned files with spaces in names

**Owner:** be (can be done by any agent since it is file deletion only)
**Priority:** p1
**Files to delete:**
- `tests/test_pipeline_hardening 2.py`
- `ops/logger 2.py`
- `frontend/app/page 2.tsx`
- `frontend/next.config 2.mjs`

**Done when:** All four files removed, git status clean, no broken imports.

---

### Ticket CL-3 -- Remove unused imports and dead constants in use_case_generator.py

**Owner:** be
**Priority:** p2
**Changes:**
- Remove `_TIER_ORDER` constant at line 19 of `agents/use_case_generator.py` (defined, never used)
- Remove `_TIER_TO_KEY` constant at line 20 (defined, never used)

**Done when:** Both constants removed, `pytest tests/ -q --tb=short` passes.

---

### Ticket CL-4 -- Remove unused import and dead function in stage_io / pipeline

**Owner:** be
**Priority:** p2
**Changes:**
- Remove `victory_output` from the import in `orchestrator/pipeline.py` (imported, never called)
- Remove `report_writer_input()` function from `orchestrator/stage_io.py` (defined, never imported)

**Done when:** Both removed, tests pass, no import errors.

---

### Ticket CL-5 -- Fix SYSTEM_STATE.md startup command

**Owner:** pm
**Priority:** p1
**Changes:**
- Fix line 46: change `uvicorn infra.app:app` to `uvicorn app:app`
- Fix line 177: change `infra/app.py` reference to `app.py` in the Sprint 6 files list

**Done when:** SYSTEM_STATE.md accurate, Sai can copy-paste the startup command and it works.

---

### Ticket CL-6 -- Evaluate and archive rag/backfill_solutions.py

**Owner:** be
**Priority:** p3
**Decision needed:** Is the Sprint 8 field migration complete and confirmed applied to `victories.json`?
If yes: delete `rag/backfill_solutions.py`.
If no: run the backfill and then delete.

**Done when:** File removed after confirming all records in `victories.json` have Sprint 8 fields.

---

### Priority Order

1. CL-1 -- delete consultant (dead module, dead tests, dead prompt)
2. CL-2 -- delete space-named files (unreachable, untracked, zero impact)
3. CL-5 -- fix docs startup command (Sai needs this to work right now)
4. CL-3 -- remove dead constants (low risk, clean code)
5. CL-4 -- remove unused imports/functions (clean code)
6. CL-6 -- backfill evaluation and archive (lower urgency)

---

## Summary Count

| Category | Count |
|----------|-------|
| Files to delete | 7 (agents/consultant.py, test_consultant.py, prompts/consultant.md, 4 space-named files) |
| Unused imports/constants | 2 (victory_output import, _TIER_ORDER, _TIER_TO_KEY) |
| Unreferenced functions | 2 (stage_io.report_writer_input, consultant.format_wins -- gone with file) |
| Duplicate logic | 2 function pairs (_proximity_score, _industries_related) -- coupled to compat path |
| Orphaned test files | 2 (test_consultant.py, test_pipeline_hardening 2.py) |
| Orphaned prompts | 1 (prompts/consultant.md) |
| Stale docs | 1 file, 2 incorrect lines (SYSTEM_STATE.md) |
| One-time scripts to evaluate | 1 (rag/backfill_solutions.py) |
