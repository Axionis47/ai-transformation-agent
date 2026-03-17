# Sprint 8 Plan

**Sprint goal:** Get all three eval dimensions above 3.8 and confirm CI/CD delivers a live Cloud Run URL.

---

## Background

Sprint 6 was the first real eval run. Scores are:

| Dimension | Sprint 6 | Target |
|-----------|----------|--------|
| tier_classification | 3.67 | >= 3.8 |
| evidence_grounding | 3.20 | >= 3.8 |
| roi_basis | 3.07 | >= 3.8 |

CI/CD workflows exist in `.github/workflows/` but the live deploy has never executed. The eval
sprint key (`_SPRINT`) in `ci_eval.py` is still hardcoded to `sprint_6`, so any new eval run
overwrites the Sprint 6 baseline instead of recording Sprint 8 results.

The eval system has a structural problem: `_uc_vars()` passes signal IDs to the judge but not
the actual signal content (value + raw_quote). The evidence_grounding judge can only see
`sig-001, sig-003, sig-006` - not what those signals contain. It cannot verify grounding.
The score is capped at 3 because the judge is guessing. Fixing the eval context, not just
the prompts, is the highest-leverage action.

---

## Ordered Ticket List

### Priority 1 - Eval System Fix (unblocks everything else)

**DISC-66: Fix eval context - pass signal content to judge**
- Owner: QA (evals/*.py)
- The `_uc_vars()` function in `ci_eval.py` must pass actual signal value+raw_quote alongside signal IDs
- Update `evidence_grounding.yaml` rubric prompt to receive and use signal content
- Update `_SPRINT` constant to `sprint_8`
- This is the highest-leverage change - raises evidence_grounding ceiling from 3 to 5

**DISC-67: Harden rubric judge prompts**
- Owner: PM (evals/rubrics/*.yaml)
- `roi_basis.yaml`: add explicit instruction that `win-NNN` format = 4 points minimum
- `tier_classification.yaml`: add explicit overlap ranges to reduce ambiguity
- `evidence_grounding.yaml`: instruction to look for raw_quote alignment with description
- All three rubric files need sharper scoring criteria at the 4/5 boundary

### Priority 2 - CI/CD Hardening

**DISC-68: Fix CI/CD reliability issues**
- Owner: QA (.github/workflows/)
- `cd.yml`: remove `|| true` from `gcloud builds submit` - it silently swallows build failures
- `ci.yml`: add push trigger for `develop` branch (currently only `main`)
- `ci.yml`: verify ruff config doesn't skip agent files
- `cd.yml`: update `SERVICE_VERSION` env var to `sprint8`
- Add a step that prints the live URL to job summary so Sai can see it

**DISC-69: Trigger first live Cloud Run deploy**
- Owner: QA (but requires Sai to set GCP_SA_KEY and GCP_PROJECT_ID secrets in GitHub)
- Flag: GCP_SA_KEY and GCP_PROJECT_ID must be set in GitHub repo secrets before this can run
- Verify smoke test curl hits /health and returns 200
- Document the live URL in SYSTEM_STATE.md

### Priority 3 - Prompt Iteration (after eval system is sound)

**DISC-70: Iterate use_case_generator prompt for score improvement**
- Owner: PM (prompts/use_case_generator.md)
- Blocked by DISC-66 (need sound eval before iterating)
- Focus: force explicit win_id citation format in roi_basis, require raw_quote reference in why_this_company
- Max 3 iterations. Run evals after each. Stop at >= 3.8 or 3 iterations.

**DISC-71: Iterate signal_extractor and maturity_scorer prompts**
- Owner: PM (prompts/signal_extractor.md, prompts/maturity_scorer.md)
- Blocked by DISC-66
- signal_extractor: improve raw_quote quality (full phrase, not truncated mid-word)
- maturity_scorer: require signals_used to include raw_quote snippets in rationale
- These feed signal quality upstream, which improves evidence_grounding scores

### Priority 4 - Frontend Low-Signal Warning

**DISC-72: Add low-signal warning banner to results page**
- Owner: Frontend (frontend/components/)
- Blocked by nothing (API already returns signal_count)
- Show yellow warning banner in ResultsView when signal_count < 3
- Banner text: "Low signal confidence - only N signals extracted. Results may be less accurate."
- Banner disappears when signal_count >= 3

### Priority 5 - LinkedIn Job Scraper Tool

**DISC-73: Add LinkedIn job scraper tool (dry-run only)**
- Owner: Backend (tools/, orchestrator/tool_registry.py)
- Create `tools/linkedin_job_scraper.py` with `LinkedInJobScraperTool`
- Dry-run only: reads from `tests/fixtures/sample_linkedin_jobs.json`
- Register in `orchestrator/tool_registry.py` alongside website_scraper
- Create fixture file with 3 sample job postings
- All existing 140 tests must still pass

---

## Dependency Graph

```
DISC-66 (eval context fix)
  -> DISC-67 (rubric prompts) - can run in parallel with DISC-66
  -> DISC-70 (use_case_generator prompt) - blocked by DISC-66
  -> DISC-71 (signal prompts) - blocked by DISC-66

DISC-68 (CI/CD hardening)
  -> DISC-69 (live deploy) - blocked by DISC-68 + Sai must set secrets

DISC-72 (low-signal banner) - no blockers
DISC-73 (LinkedIn tool) - no blockers
```

---

## What Blocks What

| Ticket | Blocked by |
|--------|-----------|
| DISC-67 | can start with DISC-66 in parallel |
| DISC-70 | DISC-66 must be merged first |
| DISC-71 | DISC-66 must be merged first |
| DISC-69 | DISC-68 + Sai sets GCP secrets |
| DISC-72 | nothing |
| DISC-73 | nothing |

---

## Sai Action Required

Before DISC-69 can execute, Sai must:
1. Go to GitHub repo Settings -> Secrets -> Actions
2. Add `GCP_SA_KEY` = the service account JSON for `ai-transform-agent@plotpointe.iam.gserviceaccount.com`
3. Add `GCP_PROJECT_ID` = `plotpointe`

The CD workflow uses these. Without them, Cloud Run deploy cannot run from CI.

---

## Success Criteria

When this sprint is done, Sai can:

1. Open the GitHub Actions tab and see CI passing on a PR to main (green badge)
2. See the CD workflow triggered automatically after CI passes
3. See the live Cloud Run URL printed in the CD job summary
4. Run `curl https://<live-url>/health` and get `{"status":"healthy",...}`
5. Submit any URL in the frontend and get a report rendered
6. See eval scores in `evals/baselines.json` under `sprint_8` key, all >= 3.8
7. See a yellow warning banner on results pages when signal_count < 3

---

## Test Count Target

Sprint 8 target: 155+ tests (currently 140, adding ~15 for DISC-72 + DISC-73).

---

## Sprint Sequence

Execute tickets in this order:

1. DISC-66 + DISC-67 + DISC-68 + DISC-72 + DISC-73 (can all start in parallel)
2. DISC-70 + DISC-71 (after DISC-66 is merged)
3. DISC-69 (after DISC-68 and Sai sets secrets)

---

## What Is NOT in This Sprint

- Authentication / API key gating (ADR-002 deferred)
- E2E timing validation (depends on live URL from DISC-69)
- New RAG seeds (no sprint-boundary fixture change approved)
- Frontend history page improvements (deferred)
