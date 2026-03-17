# Sprint 7 Tickets — "CI/CD & Quality"

**Author:** PM agent
**Date:** 2026-03-16
**Status:** Active — Sprint 7 execution tickets
**Sprint goal:** Automated CI/CD on every push, eval scores >= 3.8, live Cloud Run URL.

---

## Ticket Index

| Ticket | Owner | Title | Priority | Blocked by |
|--------|-------|-------|----------|------------|
| DISC-58 | QA | GitHub Actions CI pipeline | P1 | nothing |
| DISC-59 | Backend | Cloud Run CD pipeline + smoke test | P1 | DISC-58 |
| DISC-60 | PM | Prompt engineering — raise all eval scores above 3.8 | P1 | DISC-58 |
| DISC-61 | Backend | GCP defaults hardcoded — zero env setup on clean clone | P2 | nothing |
| DISC-62 | Frontend | Low-signal warning banner | P2 | nothing |
| DISC-63 | Backend | Production deploy — live Cloud Run URL | P1 | DISC-58, DISC-59, Sai approval |

---

## DISC-58: GitHub Actions CI Pipeline

**Owner:** QA
**Priority:** P1
**Blocked by:** nothing — starts immediately

### User story
As an engineer pushing code to this repo, I need a GitHub Actions CI workflow that
runs tests, linting, and an eval regression gate automatically on every push, so that
broken code and quality regressions are caught before they reach main.

### done_when
`.github/workflows/ci.yml` exists, runs on every push to any branch, passes
`pytest tests/ -q --tb=short` (failing if any test fails), passes ruff lint, and runs
`python evals/ci_eval.py --dry-run` comparing results against sprint_6 baselines —
failing the build if any dimension's score drops below the sprint_6 average.

### Acceptance criteria
- [ ] `.github/workflows/ci.yml` exists and triggers on `push` to all branches and
  `pull_request` targeting main
- [ ] CI step 1 — test gate: runs `pytest tests/ -q --tb=short`; workflow fails if
  any test fails; exit code propagated correctly
- [ ] CI step 2 — lint gate: runs `ruff check . --select E,F,W`; workflow fails if
  any lint error is present; existing violations fixed before gate added (so CI starts
  green, not red)
- [ ] CI step 3 — eval regression gate: runs `python evals/ci_eval.py --dry-run`;
  loads sprint_6 averages from `evals/baselines.json`; fails if any dimension score
  drops below sprint_6 average (tier_classification: 3.67, evidence_grounding: 3.20,
  roi_basis: 3.07); passes if scores are equal to or above sprint_6
- [ ] `evals/ci_eval.py` gains a `--dry-run` flag that runs against fixture data only
  (zero real API calls) and produces comparable scores for the regression gate
- [ ] `evals/gate_check.py` updated (or created if not exists) to load baselines.json
  and compare current scores against the named sprint key — returns exit code 0 if all
  pass, exit code 1 if any dimension regresses
- [ ] Python version in CI matches local: `python-version: "3.11"`
- [ ] `pip install -r requirements.txt` cached via `actions/cache` on requirements hash
  so CI runs faster on repeated pushes
- [ ] `ruff` added to `requirements.txt` if not already present
- [ ] CI workflow completes in under 3 minutes on a normal push (no model calls, no
  scraping — fixture only)
- [ ] First CI run on main branch is green — no red start (fix existing lint issues
  before adding the lint gate)
- [ ] `tests/test_ci_gate.py` exists with unit tests: gate_check returns 0 when scores
  equal baseline, returns 1 when any dimension regresses, handles missing sprint key
  gracefully

### Execute with
Primary: qa
Collaborators: none
Reason: `.github/workflows/ci.yml`, `evals/gate_check.py`, and `tests/test_ci_gate.py`
are all QA-owned files. The `--dry-run` flag addition to `ci_eval.py` is in `evals/`
which QA owns.

### Files to create/modify
- `.github/workflows/ci.yml` — new file: CI workflow (pytest + ruff + eval gate)
- `evals/ci_eval.py` — add `--dry-run` flag that uses fixture data, not live pipeline
- `evals/gate_check.py` — create or update: baseline comparison logic, exit code
- `tests/test_ci_gate.py` — new file: unit tests for gate_check
- `requirements.txt` — add ruff if missing

### Test certification required
yes

### Decision required
no

---

## DISC-59: Cloud Run CD Pipeline + Smoke Test

**Owner:** Backend
**Priority:** P1
**Blocked by:** DISC-58 (CI must exist and be green before CD workflow is added)

### User story
As Sai reviewing the system after a code merge, I need every merge to main to
automatically build a Docker image, push it to gcr.io, deploy it to Cloud Run, and
run a smoke test against `/health` — so that the live URL is always in sync with
the main branch without manual intervention.

### done_when
`.github/workflows/cd.yml` exists, triggers on push to main after CI passes, builds
and pushes the Docker image to `gcr.io/plotpointe/ai-transform-agent`, deploys to
Cloud Run in `us-central1`, and fails the workflow if `/health` does not return 200
within 30 seconds of deploy.

### Acceptance criteria
- [ ] `.github/workflows/cd.yml` exists and triggers on `push` to `main` only
  (not on PRs, not on other branches)
- [ ] CD is gated on CI passing — uses `needs: ci` or workflow ordering so CD does
  not trigger if CI fails
- [ ] CD step 1 — auth: authenticates to GCP using `google-github-actions/auth@v2`
  with `GCP_SA_KEY` GitHub secret (service account JSON for
  `ai-transform-agent@plotpointe.iam.gserviceaccount.com`)
- [ ] CD step 2 — build + push: runs `gcloud builds submit --tag gcr.io/plotpointe/ai-transform-agent`
  from repo root; image tag includes the git SHA: `gcr.io/plotpointe/ai-transform-agent:${{ github.sha }}`
- [ ] CD step 3 — deploy: runs `gcloud run deploy ai-transform-agent --image gcr.io/plotpointe/ai-transform-agent:${{ github.sha }} --platform managed --region us-central1 --allow-unauthenticated --port 8080 --min-instances 1`
  (min-instances=1 prevents cold starts that would blow the 90s SLA)
- [ ] CD step 4 — smoke test: `curl --fail --retry 3 --retry-delay 5 https://<CLOUD_RUN_URL>/health`
  exits 0 if response is 200; exits non-zero and fails the workflow otherwise
- [ ] Cloud Run URL is captured from the deploy output and used in the smoke test step
  (use `gcloud run services describe` or parse deploy output)
- [ ] `GCP_PROJECT_ID` environment variable in workflow is `plotpointe` (hardcoded, not
  a required secret — it is not sensitive)
- [ ] `GCP_SA_KEY` is a GitHub secret — workflow references it as
  `${{ secrets.GCP_SA_KEY }}`. PM has documented what Sai must add in the escalation
  comment on this ticket.
- [ ] CD workflow does NOT commit or push to main — it only builds and deploys
- [ ] `infra/deploy_target.py` is not bypassed — the CD workflow calls the same
  gcloud commands that `deploy_target.py` wraps, ensuring the abstraction is in sync
- [ ] If smoke test fails, workflow exit code is non-zero — Sai gets a GitHub
  Actions notification of deploy failure

### Execute with
Primary: backend
Collaborators: qa (adds smoke test step to workflow — crosses into .github/workflows/)
Reason: infra/deploy_target.py and gcloud CLI logic are backend-owned. The CD
workflow (.github/workflows/cd.yml) is QA-owned but the gcloud commands inside it
are backend domain knowledge. Backend writes the workflow, QA reviews the smoke test
step.

### Files to create/modify
- `.github/workflows/cd.yml` — new file: CD workflow (build, push, deploy, smoke test)

### Tier 2 escalation — Sai must add GitHub secret
PM will post a Tier 2 escalation comment on this ticket:
- Secret name: `GCP_SA_KEY`
- Secret value: contents of `service_account.json` for `ai-transform-agent@plotpointe.iam.gserviceaccount.com`
- Where to add: GitHub repo → Settings → Secrets and variables → Actions → New repository secret

CD workflow cannot pass until this secret is set. PM escalates this to Sai before
DISC-59 starts execution.

### Test certification required
yes — smoke test in CD workflow counts as certification (green deploy + /health 200)

### Decision required
no (CD strategy was decided in ADR-010 — Cloud Run as production deploy target)

---

## DISC-60: Prompt Engineering — Raise All Eval Scores Above 3.8

**Owner:** PM
**Priority:** P1
**Blocked by:** DISC-58 (CI must be running so each prompt iteration is auto-evaluated)

### User story
As Sai presenting the system to Tenex, I need all three eval dimensions to score
above 3.8/5.0 so that when a Tenex engineer asks "how do you know the output is
good?" I can point to automated eval scores measured against a consistent rubric.

### done_when
`evals/baselines.json` contains a `sprint_7` key where all three dimension averages
are >= 3.8 (tier_classification, evidence_grounding, roi_basis), and the scores were
produced by running `evals/ci_eval.py` against the same 5 test companies used in
sprint_6.

### Context: Sprint 6 scores and gaps

| Dimension | Sprint 6 Avg | Gap | Likely cause |
|-----------|-------------|-----|--------------|
| tier_classification | 3.67 | +0.13 | Tier assignment logic is mostly correct — minor calibration needed |
| evidence_grounding | 3.20 | +0.60 | Report sections don't cite signal IDs explicitly enough |
| roi_basis | 3.07 | +0.73 | use_cases roi_basis field uses generic language; win_id + gap_analysis not cited |

### Acceptance criteria
- [ ] `prompts/report_writer.md` updated: explicitly instructs the model to cite
  evidence_signal_ids when making claims in executive summary and findings sections;
  adds instruction: "For every claim about the company's current state, cite the
  specific signal ID from the evidence_signals list that supports it."
- [ ] `prompts/use_case_generator.md` updated: explicitly instructs the model to
  cite the win_id from the matched victory in every roi_basis field; adds instruction:
  "The roi_basis field must include: (1) the win_id of the matched victory, (2) the
  industry_benchmark from that victory, (3) the gap_analysis sentence."
- [ ] `prompts/consultant.md` reviewed and updated if tier_classification scores do
  not reach 3.8 after report_writer and use_case_generator prompt improvements
- [ ] Each prompt version incremented in the file header (e.g., version 1.0 → 1.1 → 1.2)
  and logged in `prompts/VERSIONS.md`
- [ ] `evals/ci_eval.py` run after each prompt update — scores recorded in output comment
  for PM review (3 iterations maximum per CLAUDE.md rules)
- [ ] `evals/baselines.json` `sprint_7` key added after the final iteration:
  ```json
  "sprint_7": {
    "run_date": "2026-03-16",
    "companies": { ... },
    "averages": {
      "tier_classification": >= 3.8,
      "evidence_grounding": >= 3.8,
      "roi_basis": >= 3.8
    }
  }
  ```
- [ ] If after 3 iterations any dimension is still below 3.8, PM posts a Tier 2
  escalation to Sai with: which dimension, the 3 scores across iterations, recommended
  next approach (rubric revision vs. data quality vs. model swap)
- [ ] `prompts/VERSIONS.md` updated with all prompt versions changed in this ticket

### Execute with
Primary: pm (prompts are PM-owned per CLAUDE.md file ownership rules)
Collaborators: backend (runs `evals/ci_eval.py` to validate scores after each iteration)
Reason: prompts/*.md files are PM-owned. Backend collaborates only to run the eval
script and confirm scores — Backend does not modify prompt files.

### Files to create/modify
- `prompts/report_writer.md` — update instructions for evidence grounding
- `prompts/use_case_generator.md` — update instructions for roi_basis citation
- `prompts/consultant.md` — update if tier_classification needs adjustment
- `prompts/VERSIONS.md` — log all version increments
- `evals/baselines.json` — add sprint_7 key with final scores

### Test certification required
yes — `evals/ci_eval.py` output showing sprint_7 averages >= 3.8 in baselines.json

### Decision required
no (prompt iteration is PM routine work, not an architecture decision)

---

## DISC-61: GCP Defaults Hardcoded — Zero Env Setup on Clean Clone

**Owner:** Backend
**Priority:** P2
**Blocked by:** nothing — starts immediately

### User story
As an engineer cloning this repo for the first time, I need to run
`python orchestrator/pipeline.py --dry-run` with zero environment variable setup
so that onboarding takes seconds, not minutes of environment configuration.

### done_when
`python orchestrator/pipeline.py --dry-run` exits 0 on a clean clone with no
`.env` file and no exported environment variables. GCP project (`plotpointe`),
GCP location (`us-central1`), and model provider (`vertex`) are all resolved from
in-code defaults when environment variables are absent.

### Acceptance criteria
- [ ] `ops/model_client.py` has default values for: `GCP_PROJECT_ID` (default: `plotpointe`),
  `GCP_LOCATION` (default: `us-central1`), `MODEL_PROVIDER` (default: `vertex`),
  `VERTEX_MODEL` (default: `gemini-2.5-pro`), `VERTEX_FAST_MODEL` (default: `gemini-2.5-flash`)
  — `os.getenv("KEY", "default")` pattern, not `os.environ["KEY"]` which raises on missing
- [ ] `evals/judge_client.py` has default values for: `GCP_PROJECT_ID` (default: `plotpointe`),
  `GCP_LOCATION` (default: `us-central1`) — same pattern
- [ ] Any other file that reads GCP-related env vars uses `os.getenv(key, default)` pattern
- [ ] `.env.example` updated to clearly mark which variables have defaults and which are
  required (use inline comment: `# Default: plotpointe — override if using a different project`)
- [ ] `README.md` Quick Start section updated: shows that dry-run requires zero env setup;
  real pipeline requires only `GCP credentials` (gcloud auth, not exported env vars)
- [ ] `python orchestrator/pipeline.py --dry-run` exits 0 with no env vars set in a
  clean shell (tested by running `env -i python orchestrator/pipeline.py --dry-run`)
- [ ] All 140 existing tests still pass after this change (no regressions from default
  value changes)
- [ ] No hardcoded secrets — only non-sensitive defaults (project ID, region, model
  names are not secrets)

### Execute with
Primary: backend
Collaborators: none
Reason: ops/model_client.py, evals/judge_client.py, and all Python files with env
var reads are backend-owned. README.md update is in scope as it describes setup steps
that are the direct result of this backend change.

### Files to create/modify
- `ops/model_client.py` — replace os.environ[] with os.getenv(key, default) pattern
- `evals/judge_client.py` — add GCP project/location defaults
- `.env.example` — annotate which vars have defaults
- `README.md` — update Quick Start with zero-setup dry-run instructions

### Test certification required
yes — `env -i python orchestrator/pipeline.py --dry-run` exits 0

### Decision required
no (hardcoding non-sensitive defaults is an implementation detail, not an architecture decision)

---

## DISC-62: Low-Signal Warning Banner

**Owner:** Frontend
**Priority:** P2
**Blocked by:** nothing (signal_count is already in the API response from Sprint 6)

### User story
As Sai reviewing a report for a thin-website company, I need a yellow warning banner
that tells me the signal count was low so that I understand why the report is more
generic than usual — and can set appropriate expectations with a client.

### done_when
When the `/v1/analyze` response includes `signal_count < 3`, a yellow banner appears
in the UI above the report sections reading: "Low signal warning: only N signals were
extracted from this company's website. Results may be less specific than usual."

### Acceptance criteria
- [ ] `LowSignalBanner` component exists at `frontend/app/components/LowSignalBanner.tsx`
- [ ] Banner is yellow (`bg-yellow-100 border-yellow-400 text-yellow-800` in Tailwind,
  or neomorphic amber styling consistent with the existing design system)
- [ ] Banner text: "Low signal warning: only {signal_count} signal{s} extracted from
  this website. Report may be less specific than usual." (pluralize "signal" correctly)
- [ ] Banner renders when `signal_count < 3` and is hidden when `signal_count >= 3`
- [ ] `signal_count` is already present in the analyze API response — frontend reads
  it from the existing response shape (no API change needed)
- [ ] Banner renders in `frontend/app/page.tsx` between the URL input form and the
  report sections — positioned above the report so it is seen before reading results
- [ ] Banner has a dismiss button (X icon) — once dismissed, it stays hidden for that
  session (local state, not persisted)
- [ ] Banner does NOT render during loading state — only after response is received
  and signal_count is known
- [ ] No TypeScript errors on build
- [ ] Storybook story exists at `frontend/stories/LowSignalBanner.stories.tsx` with
  two story states: signal_count = 1 (banner visible) and signal_count = 5 (banner hidden)

### Execute with
Primary: frontend
Collaborators: none
Reason: LowSignalBanner.tsx and page.tsx modifications are frontend-owned TypeScript
files. The signal_count field is already in the API response — no backend change needed.

### Files to create/modify
- `frontend/app/components/LowSignalBanner.tsx` — new component
- `frontend/app/page.tsx` — render LowSignalBanner between form and report sections
- `frontend/stories/LowSignalBanner.stories.tsx` — new Storybook story

### Test certification required
yes (Storybook story renders both states without TypeScript errors)

### Decision required
no

---

## DISC-63: Production Deploy — Live Cloud Run URL

**Owner:** Backend
**Priority:** P1
**Blocked by:** DISC-58 (CI must pass), DISC-59 (CD workflow must exist), Sai approval (Tier 3)

### User story
As Sai walking into the Tenex interview, I need a public Cloud Run URL where the
AI Transformation Discovery Agent is live, so that I can demo it from any machine
without setting up a local dev environment.

### done_when
`https://<cloud-run-url>/health` returns `{"pipeline": "ready", "version": "sprint7"}`
with HTTP 200, and `https://<cloud-run-url>` serves the frontend report UI.

### Tier 3 escalation — Sai approval required

Per CLAUDE.md deploy rules: "Deploy requires explicit Sai approval comment."

PM will post a Tier 3 escalation to Sai before this ticket executes:
- What will be deployed: `gcr.io/plotpointe/ai-transform-agent` at current main HEAD
- Deploy target: Cloud Run, region `us-central1`, project `plotpointe`
- Cost: Cloud Run billing is per-request; min-instances=1 means ~$5–10/month idle cost
- Rollback: `gcloud run services update-traffic --to-revisions=PREVIOUS=100`
- Approval required: Sai posts "approved" on this Linear ticket before execution

### Acceptance criteria
- [ ] Sai has posted "approved" on this Linear ticket (Tier 3 gate — ticket cannot
  start without this)
- [ ] `gcloud run deploy` executed using `infra/deploy_target.py` (not bypassing the
  abstraction layer)
- [ ] Live URL documented in: `docs/SYSTEM_STATE.md`, `README.md`, and as a comment
  on this ticket
- [ ] `curl https://<live-url>/health` returns HTTP 200 with body `{"pipeline": "ready", "version": "sprint7"}`
- [ ] `infra/health_check.py` updated: `version` field returns `"sprint7"` (was
  `"sprint6"`)
- [ ] Frontend is served at the root path — submitting a company URL via the UI on
  the live Cloud Run instance returns a report within 90 seconds
- [ ] Cost per run confirmed <= $0.50 (Vertex AI billing for a full pipeline run —
  log the cost in the output comment)
- [ ] Cloud Run service is configured with `--min-instances 1` to prevent cold start
  latency spikes
- [ ] Live URL added to `README.md` under a "Live Demo" section at the top of the file
- [ ] `docs/SYSTEM_STATE.md` updated: Live URL row added to "What Works" table

### Execute with
Primary: backend
Collaborators: none
Reason: infra/deploy_target.py, infra/health_check.py, and the gcloud deploy commands
are all backend-owned. README and SYSTEM_STATE updates are in scope as they document
the result of this backend operation.

### Files to create/modify
- `infra/health_check.py` — update version field to "sprint7"
- `docs/SYSTEM_STATE.md` — add live URL to "What Works" table
- `README.md` — add "Live Demo" section with live URL at top of file

### Test certification required
yes — `curl https://<live-url>/health` returns 200 with correct body

### Decision required
no (deploy target decided in ADR-010)

---

## Carried Ticket: DISC-55 (P3 — Deferred Again if Needed)

**DISC-55:** LinkedInJobScraper (second tool registration)
**Original sprint:** Sprint 6
**Carried to:** Sprint 7 as P3
**Status:** Defer again if Sprint 7 P1s are at risk

This ticket adds a second tool to the tool registry. It requires LinkedIn scraping
(requires playwright or requests-html for JS rendering) and dry-run fixture support.
Given Sprint 7's CI/CD and eval score priorities, this is the first cut if the sprint
runs long.

If DISC-55 carries to Sprint 8, PM will declare it the final window — the second tool
must ship before Tenex submission.

---

## Cross-Ticket Notes

### CI/CD ordering — strictly sequential

DISC-58 (CI) must complete and be green before DISC-59 (CD) starts. The CD workflow
references the CI workflow. Running both in parallel would require CD to reference a
CI workflow that does not yet exist, causing a workflow parse error on first push.

### GCP secret dependency for CD

The CD workflow (DISC-59) requires `GCP_SA_KEY` to be set as a GitHub Actions secret
before any merge to main can trigger a successful CD run. PM escalates this to Sai
(Tier 2) as soon as DISC-58 ships. The escalation comment includes exact secret names
and instructions for Sai to add them in GitHub repo settings.

### Eval dry-run mode for CI

DISC-58 requires `evals/ci_eval.py` to support `--dry-run` mode. In dry-run mode,
the eval script uses fixture data from `tests/fixtures/` rather than calling the live
pipeline. This means the eval scores in CI are computed from the same fixture outputs
every run — making the regression gate deterministic. The fixture-based scores must
be >= sprint_6 averages, otherwise the CI gate would fail on every push regardless of
prompt changes.

The dry-run eval scores will differ from the live eval scores (fixture data is simpler
than real scraped content). The sprint_7 baselines.json key is populated from a live
eval run (not dry-run), performed by PM as part of DISC-60. The CI gate uses dry-run
scores as a regression floor only — not as the official sprint score.

### Frontend and Backend never run simultaneously

Per CLAUDE.md rules, Backend and Frontend subagents never run at the same time.
- DISC-62 (Frontend) must not execute at the same time as DISC-59 or DISC-61 (Backend)
- Recommended sequencing: DISC-61 (Backend) → then DISC-62 (Frontend)

---

## Sprint 7 Definition of Done

- [ ] `pytest tests/ -q --tb=short` passes — 140+ tests, zero regressions
- [ ] `.github/workflows/ci.yml` runs on every push and fails fast on test or lint errors
- [ ] `evals/ci_eval.py --dry-run` is part of CI and fails on eval regressions
- [ ] `.github/workflows/cd.yml` runs on main merge and deploys to Cloud Run automatically
- [ ] Live Cloud Run URL is documented in README.md and SYSTEM_STATE.md
- [ ] `curl https://<live-url>/health` returns HTTP 200
- [ ] `evals/baselines.json` sprint_7 key shows all averages >= 3.8
- [ ] Low-signal warning banner renders in UI when signal_count < 3
- [ ] `python orchestrator/pipeline.py --dry-run` exits 0 with zero env setup
- [ ] QA sign-off comment posted with: test count, eval scores, live URL,
  CI/CD green status, regression check, and "How to Test" instructions for Sai
