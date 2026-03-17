# Sprint 7 — CI/CD & Quality

**Author:** PM agent
**Date:** 2026-03-16
**Status:** Active sprint plan — approved for execution
**North star:** Every push to main triggers automated tests and a live deploy to Cloud
Run. All three eval dimensions cross 3.8. Sai clicks a public URL, submits a company,
and gets a scored report — no localhost required.

---

## Sprint Goal

"CI/CD & Quality" — automate the delivery pipeline and raise eval scores above the
quality bar.

Sprint 6 shipped parallel report writes, an extended scraper, a Dockerfile, and the
Cloud Run deploy target. Three things are still broken: there is no automated CI gate
(every push is untested by default), eval scores across all three dimensions are below
the 3.8 threshold (tier_classification: 3.67, evidence_grounding: 3.20, roi_basis:
3.07), and the system has no live public URL.

Sprint 7 closes all three gaps, in that order.

---

## What Sai Sees at Sprint End

1. Push any code to main → GitHub Actions runs tests + eval regression gate automatically
2. CI passes → CD workflow builds Docker image, pushes to gcr.io, deploys to Cloud Run
3. Sai visits the live Cloud Run URL → submits a company → report renders in under 90s
4. `cat evals/baselines.json` → sprint_7 key shows all three averages >= 3.8
5. Submit a URL for a company with few web signals → yellow warning banner appears in UI
6. `pytest tests/ -q --tb=short` → 140+ tests pass (no regressions)

---

## Context: What Sprint 6 Left Us

| Component | State |
|-----------|-------|
| 7-stage pipeline | Working — 140 tests passing, zero regressions |
| POST /v1/analyze | Live endpoint — returns signals, maturity, victory_matches, use_cases, report |
| GET /v1/trace/{run_id} | Live — trace panel in UI reads from it |
| Parallel report writes | Working — ThreadPoolExecutor(max_workers=3) |
| Extended scraper | Working — fetches /about, /careers, /products, /solutions, /platform |
| pages_fetched + signal_count | In API response — low-signal detection is ready server-side |
| Eval scores (sprint_6) | tier_classification: 3.67, evidence_grounding: 3.20, roi_basis: 3.07 — ALL BELOW 3.8 |
| Eval judge | Switched to Gemini (gemini-2.5-pro on Vertex AI) — working |
| Dockerfile | At repo root — build confirmed |
| Cloud Run deploy target | infra/deploy_target.py implemented — not yet executed live |
| GitHub Actions CI | Not built — zero automated test gate on push |
| Low-signal UI warning | signal_count in API; frontend banner not built |
| GCP project | plotpointe — hardcoded in judge_client.py; env var not required |

---

## Sprint 7 Tickets

| Ticket | Owner | Title | Priority | Blocked by |
|--------|-------|-------|----------|------------|
| DISC-58 | QA | GitHub Actions CI pipeline | P1 | nothing |
| DISC-59 | Backend | Cloud Run CD pipeline + smoke test | P1 | DISC-58 |
| DISC-60 | PM | Prompt engineering — raise all eval scores above 3.8 | P1 | DISC-58 (needs CI to run evals) |
| DISC-61 | Backend | GCP defaults hardcoded — zero env setup on clean clone | P2 | nothing |
| DISC-62 | Frontend | Low-signal warning banner | P2 | nothing |
| DISC-63 | Backend | Production deploy — live Cloud Run URL (Tier 3) | P1 | DISC-58, DISC-59 |

---

## Dependency Graph

```
DISC-58 (QA: CI pipeline)
    ├── DISC-59 (Backend: CD pipeline — triggers after CI passes)
    └── DISC-60 (PM: prompt engineering — needs CI to validate eval gate)

DISC-61 (Backend: GCP defaults) — no blocking deps, parallel
DISC-62 (Frontend: warning banner) — no blocking deps, parallel

DISC-63 (Backend: live deploy) — blocked by DISC-58 and DISC-59
    [Tier 3: requires Sai approval before execution]
```

### Why these dependencies

- DISC-59 (CD) must come after DISC-58 (CI). The CD workflow is triggered by a
  successful CI run on main. No CI gate means the CD workflow could deploy broken code.
  CD is a downstream consequence of CI, not an independent workflow.

- DISC-60 (prompt engineering) needs CI to be in place so that each prompt iteration
  can be validated by the eval gate automatically. The prompt engineer iterates → pushes
  → CI runs evals → passes or fails. Without CI, prompt iterations are manual and hard
  to verify at scale.

- DISC-63 (live deploy) requires both CI (DISC-58) and CD (DISC-59) to exist before
  executing the first production deploy. It also requires Sai's explicit approval
  (Tier 3 escalation) per CLAUDE.md deploy rules.

- DISC-61 and DISC-62 have no blocking dependencies. They are P2 and can run in
  parallel with or after the P1 tickets.

---

## Execution Order

```
Wave 1 — No dependencies (start immediately):
  DISC-58 (QA):      GitHub Actions CI pipeline
  DISC-61 (Backend): GCP defaults hardcoded (parallel — no dependency)
  DISC-62 (Frontend): Low-signal warning banner (parallel — no dependency)

Wave 2 — Blocked by Wave 1:
  DISC-59 (Backend): CD pipeline
                     [blocked by DISC-58 — CI must exist before CD]
  DISC-60 (PM):      Prompt engineering
                     [blocked by DISC-58 — CI runs evals on each push]

Wave 3 — Blocked by Wave 2 + Sai approval:
  DISC-63 (Backend): Production deploy
                     [blocked by DISC-58, DISC-59 + Tier 3 Sai approval]
```

Recommended execution sequence for a single agent working serially:
1. DISC-58 (QA — no deps, P1, unblocks two other tickets)
2. DISC-61 (Backend — no deps, P2, fast, easy win)
3. DISC-59 (Backend — P1, unblocks live deploy)
4. DISC-62 (Frontend — P2, no deps, runs any time)
5. DISC-60 (PM — P1, iterative, needs CI in place)
6. DISC-63 (Backend — P1, last, requires Sai approval)

Note: Backend and Frontend never run simultaneously. DISC-62 (Frontend) must not
run at the same time as DISC-59 or DISC-61 (Backend).

---

## Eval Score Targets (Sprint 7 Quality Gate)

| Dimension | Sprint 6 Average | Sprint 7 Target | Gap to close |
|-----------|-----------------|-----------------|--------------|
| tier_classification | 3.67 | >= 3.8 | +0.13 |
| evidence_grounding | 3.20 | >= 3.8 | +0.60 |
| roi_basis | 3.07 | >= 3.8 | +0.73 |

evidence_grounding and roi_basis need the most work. These dimensions measure whether
the output cites specific signals and victory IDs — a prompt engineering problem, not
an architecture problem. The gap analysis fields added in Sprint 5 (DISC-47, DISC-51)
are present in the pipeline; they are just not being surfaced clearly enough in the
prompts.

Primary prompt files to iterate on:
- `prompts/consultant.md` — signal extraction and maturity scoring instructions
- `prompts/report_writer.md` — evidence grounding in the five report sections
- `prompts/use_case_generator.md` — roi_basis citing win_ids and gap analysis

Each iteration: update prompt → run `evals/ci_eval.py` → compare scores to sprint_6
baseline → continue or stop (3 iterations max per CLAUDE.md rules).

---

## CI/CD Architecture

```
On push to any branch:
  .github/workflows/ci.yml
    → pytest tests/ -q --tb=short         (fail if any test fails)
    → ruff check . --select E,F,W         (lint gate)
    → python evals/ci_eval.py --dry-run   (eval regression gate vs sprint_6 baselines)

On merge to main (after CI passes):
  .github/workflows/cd.yml
    → docker build + push to gcr.io/plotpointe/ai-transform-agent
    → gcloud run deploy ai-transform-agent
    → curl /health on live URL — fail if not 200
```

GitHub Secrets required for CD:
- `GCP_SA_KEY` — service account JSON for `ai-transform-agent@plotpointe.iam.gserviceaccount.com`
- `GCP_PROJECT_ID` — `plotpointe`

Sai must add these secrets to the GitHub repo settings before DISC-59 can execute.
This is a Tier 2 escalation: PM surfaces to Sai with the exact secret names and
values needed. Sai adds them. CD workflow then works automatically.

---

## Sprint 7 Definition of Done

- [ ] `.github/workflows/ci.yml` runs on every push: pytest, ruff, eval regression gate
- [ ] `.github/workflows/cd.yml` runs on merge to main: build, push, deploy, smoke test
- [ ] All three eval dimensions average >= 3.8 in `evals/baselines.json` sprint_7 key
- [ ] Live Cloud Run URL returns 200 on `/health`
- [ ] Submit a URL on the live Cloud Run UI → report renders within 90 seconds
- [ ] Low-signal warning banner (yellow) appears when signal_count < 3
- [ ] `pytest tests/ -q --tb=short` shows 140+ tests, zero regressions
- [ ] GCP defaults hardcoded — `python orchestrator/pipeline.py --dry-run` works with
  zero env var setup on a clean clone
- [ ] README updated with live URL and simplified setup instructions
- [ ] QA sign-off comment posted with: test count, eval scores, live URL, regression status

**The rule: if Sai cannot open the live URL, submit a company, and see a scored report
with passing eval dimensions — Sprint 7 is not done.**

---

## Visible Deliverables for Sai to Test

| What | How Sai tests it |
|------|-----------------|
| CI pipeline | Push any commit → go to GitHub Actions tab → see pytest + eval gate run |
| CD pipeline | Merge a PR to main → CI passes → CD deploys → live URL updates |
| Live URL | Visit Cloud Run URL → submit a company URL → report renders in < 90s |
| Eval scores | `cat evals/baselines.json` → sprint_7 averages all >= 3.8 |
| Low-signal warning | Submit a thin-website company → yellow banner appears above report |
| Zero env setup | Clone repo → `python orchestrator/pipeline.py --dry-run` → exits 0 |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GCP_SA_KEY secret not added by Sai before DISC-59 | Medium | High | PM escalates to Sai (Tier 2) immediately when DISC-58 ships. CD cannot merge without secret. |
| Eval scores don't reach 3.8 after 3 prompt iterations | Medium | Medium | After 3 iterations, PM escalates to Sai (Tier 2 per CLAUDE.md rules). Do not block sprint on this. |
| Ruff lint fails on existing code | Low | Low | Run `ruff check . --select E,F,W --fix` during DISC-58 — fix any existing violations before adding the lint gate. |
| Cloud Run cold start adds latency beyond 90s | Low | Medium | Cloud Run minimum instances=1 to prevent cold starts — add flag to gcloud run deploy command. |
| Parallel CI + CD workflows hit GCP quota | Low | Low | CD only triggers on main merge — low frequency. CI only tests, no GCP calls. No quota risk. |

---

## What Sprint 8 Depends On

Sprint 8 cannot plan until Sprint 7 establishes:
- Live URL — Sprint 8 E2E testing must run against the live endpoint, not localhost
- eval scores >= 3.8 — Sprint 8 cannot regress below this quality floor
- CI/CD — Sprint 8 every ticket is gated by CI automatically, no manual verification

If DISC-55 (LinkedInJobScraper) carries again, Sprint 8 is its final window.
The second tool must ship before Tenex submission.

