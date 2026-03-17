# Sprint 6 Tickets — "Ship It"

**Author:** PM agent
**Date:** 2026-03-16
**Status:** Active — Sprint 6 execution tickets
**Sprint goal:** Real eval scores, richer signals, parallel writes, deploy to Cloud Run.

---

## Ticket Index

| Ticket | Owner | Title | Priority | Blocked by |
|--------|-------|-------|----------|------------|
| DISC-52 | QA | Run real eval baseline — populate baselines.json with live judge scores | P1 | nothing |
| DISC-53 | Backend | Extend scraper to fetch product, solutions, and platform pages | P1 | nothing |
| DISC-54 | Backend | Parallel report section writes via asyncio.gather | P1 | nothing |
| DISC-55 | Backend | Register LinkedInJobScraper as second tool in tool registry | P2 | DISC-53 |
| DISC-56 | Frontend | Low-signal confidence warning banner in UI | P2 | DISC-53 |
| DISC-57 | Backend | Cloud Run deploy: Dockerfile + deploy target + CI smoke test | P1 | DISC-52, DISC-54 |

---

## DISC-52: Real Eval Baseline

**Owner:** QA
**Priority:** P1
**Blocked by:** nothing — starts immediately (requires ANTHROPIC_API_KEY in env)

### User story
As Sai reviewing sprint quality, I need real numeric eval scores in
`evals/baselines.json` under a `sprint_6` key so that Sprint 7 has a measurable
quality floor and any prompt engineering regressions are detectable.

### done_when
`evals/baselines.json` contains a `sprint_6` key with real scores (not 0.0) for
all 5 test companies across all 3 rubric dimensions, produced by running
`ANTHROPIC_API_KEY=<key> python evals/ci_eval.py` against the dry-run pipeline.

### Acceptance criteria
- [ ] `evals/ci_eval.py` invoked with `ANTHROPIC_API_KEY` set in environment — exits 0
- [ ] `evals/baselines.json` updated with a `sprint_6` key alongside the existing
  `sprint_5` key:
  ```json
  {
    "sprint_5": { ... },
    "sprint_6": {
      "run_date": "2026-03-16",
      "companies": {
        "cargoLogik":       { "tier_classification": X.X, "evidence_grounding": X.X, "roi_basis": X.X },
        "healthTech":       { "tier_classification": X.X, "evidence_grounding": X.X, "roi_basis": X.X },
        "retailBrand":      { "tier_classification": X.X, "evidence_grounding": X.X, "roi_basis": X.X },
        "fintechStartup":   { "tier_classification": X.X, "evidence_grounding": X.X, "roi_basis": X.X },
        "professionalSvc":  { "tier_classification": X.X, "evidence_grounding": X.X, "roi_basis": X.X }
      },
      "averages": {
        "tier_classification": X.X,
        "evidence_grounding": X.X,
        "roi_basis": X.X
      }
    }
  }
  ```
  (X.X replaced with real scores from the judge run)
- [ ] Each score is a float between 1.0 and 5.0 — not 0.0, not null
- [ ] `tests/test_evals.py` updated: adds a test that verifies `sprint_6` key exists
  in baselines.json and that all averages are > 0.0
- [ ] If any dimension average is below 3.8 (EVAL_PASS_THRESHOLD), QA posts a flag
  comment on the ticket identifying which dimension failed and tagging PM for
  Tier 2 escalation decision
- [ ] All 117 Sprint 5 tests still pass
- [ ] Output comment includes the actual numeric scores (not just "PASSED")

### Execute with
Primary: qa
Collaborators: none
Reason: evals/ci_eval.py, evals/baselines.json, and tests/test_evals.py are all
QA-owned files. This is a run-and-record task — no new code agent files involved.

### Files to create/modify
- `evals/baselines.json` — add `sprint_6` key with real scores from judge run
- `tests/test_evals.py` — add assertion that sprint_6 key exists with non-zero scores

### Test certification required
yes — output comment must include the actual scores, not just "test passed"

### Decision required
no

### Blocked by
nothing

---

## DISC-53: Extended Scraper — Product and Solutions Pages

**Owner:** Backend
**Priority:** P1
**Blocked by:** nothing — starts immediately

### User story
As a consultant agent receiving scraped signals, I need the scraper to fetch product,
solutions, and platform pages in addition to about and careers pages so that companies
with strong product web presence produce >= 5 signals rather than <= 3, leading to
more accurate maturity scoring.

### done_when
`agents/scraper.py` fetches up to 5 candidate pages per domain (`/about`, `/careers`,
`/products`, `/solutions`, `/platform`) concurrently using asyncio, skips pages that
return 404 or timeout, merges all content into a single `company_data` dict, and a
dry-run on a product-rich fixture returns >= 5 extracted signals.

### Acceptance criteria
- [ ] `agents/scraper.py` updated: page fetch logic refactored to a list of candidate
  paths `["/about", "/careers", "/products", "/solutions", "/platform"]` — not
  hardcoded sequential requests
- [ ] All candidate pages fetched concurrently with `asyncio.gather` using
  `httpx.AsyncClient`; each page has an individual timeout of 8 seconds
- [ ] Pages returning 404, 403, or connection timeout are silently skipped — no
  exception raised, no pipeline failure; skipped pages logged at DEBUG level with
  `ops/logger.py`
- [ ] All page content merged before signal extraction: text is concatenated with a
  `\n\n---\n\n` separator between pages so signal extractor sees one unified content
  block
- [ ] `company_data` dict returned by scraper gains two new fields:
  - `pages_fetched: list[str]` — list of paths that returned 200 (e.g. `["/about", "/products"]`)
  - `signal_count_estimate: int` — count of non-empty content blocks extracted
- [ ] `POST /v1/analyze` response body gains `pages_fetched` and `signal_count` at
  the top level (extracted from scraper output) so the frontend can read them
- [ ] Dry-run mode: uses fixture data for all pages; `tests/fixtures/sample_company.json`
  updated to include a `products_page_content` field with mock product-page text
- [ ] Unit test in `tests/test_scraper.py` covers:
  - Concurrent fetch: mock httpx to return content for `/about` and `/products`,
    404 for `/solutions` — assert only the two successful pages appear in `pages_fetched`
  - Timeout skip: mock one page to raise `httpx.TimeoutException` — assert pipeline
    does not raise and skipped page is absent from `pages_fetched`
  - Content merge: two pages returned → content block contains both separated by `---`
- [ ] All 117 Sprint 5 tests still pass

### Execute with
Primary: backend
Collaborators: none
Reason: agents/scraper.py and tests/test_scraper.py are backend-owned Python files.
The `pages_fetched` and `signal_count` additions to the API response require updating
`infra/app.py` response mapping — also backend-owned.

### Files to create/modify
- `agents/scraper.py` — refactor page fetching to concurrent multi-page pattern
- `infra/app.py` — map `pages_fetched` and `signal_count` into the analyze response
- `tests/fixtures/sample_company.json` — add `products_page_content` field
- `tests/test_scraper.py` — add concurrent fetch, timeout skip, and merge tests

### Test certification required
yes

### Decision required
no (additive change to existing scraper — no architecture decision required)

### Blocked by
nothing

---

## DISC-54: Parallel Report Section Writes

**Owner:** Backend
**Priority:** P1
**Blocked by:** nothing — starts immediately (independent of DISC-53)

### User story
As Sai demoing to Tenex interviewers, I need the full 5-section report to render in
under 90 seconds so that the demo feels like a real product and not a development
prototype waiting on sequential LLM calls.

### done_when
`orchestrator/pipeline.py` generates all 5 report sections using `asyncio.gather`
instead of sequential awaits, and a measured dry-run shows at least 30% reduction
in report write time compared to the sequential baseline recorded before this ticket.

### Acceptance criteria
- [ ] `orchestrator/pipeline.py` REPORT_WRITER stage refactored: instead of calling
  the report writer agent 5 times sequentially, uses `asyncio.gather` to dispatch
  all 5 section writes concurrently
- [ ] A `asyncio.Semaphore(3)` wraps each concurrent Vertex AI call — no more than 3
  live model calls at once (prevents rate-limit errors on Vertex AI quota)
- [ ] If any single section write fails (AgentError), the pipeline catches the error
  for that section only, sets that section's content to `None`, logs the failure via
  `ops/logger.py`, and continues — the other 4 sections are not affected
- [ ] Fallback: if `asyncio.gather` raises an unexpected exception, pipeline falls
  back to sequential writes for that run and logs `parallel_fallback=True`
- [ ] `orchestrator/pipeline.py` logs two new entries via `ops/logger.py`:
  - Before gather: `event="report_parallel_start"` with `section_count=5`
  - After gather: `event="report_parallel_complete"` with `elapsed_ms` and
    `sections_succeeded` count
- [ ] `tests/test_pipeline.py` updated: adds a test that mocks the report writer agent
  and asserts `asyncio.gather` is called once (not 5 sequential calls) during the
  REPORT_WRITER stage
- [ ] Dry-run baseline time recorded in the output comment: before and after parallel
  change (measured with `time python orchestrator/pipeline.py --dry-run`)
- [ ] All 117 Sprint 5 tests still pass

### Execute with
Primary: backend
Collaborators: none
Reason: orchestrator/pipeline.py and tests/test_pipeline.py are backend-owned Python
files. The asyncio refactor is self-contained within the pipeline stage.

### Files to create/modify
- `orchestrator/pipeline.py` — refactor REPORT_WRITER stage to asyncio.gather + semaphore
- `tests/test_pipeline.py` — add parallel write assertion test

### Test certification required
yes — output comment must include before/after dry-run timing numbers

### Decision required
yes — ADR-009 required: "Parallel report section writes with semaphore-bounded concurrency"
— documents why semaphore is set to 3, why per-section failure is non-fatal, and
why sequential fallback is retained.

### Blocked by
nothing

---

## DISC-55: LinkedInJobScraper Tool Registration

**Owner:** Backend
**Priority:** P2
**Blocked by:** DISC-53 (scraper multi-page pattern must be stable before adding a second
tool that follows the same fetch pattern)

### User story
As a backend engineer extending the signal pool in Sprint 7, I need a second registered
tool — `LinkedInJobScraper` — so that future sprints can activate live job-posting
signal extraction without modifying pipeline.py or the tool registry interface.

### done_when
`tools/linkedin_job_scraper.py` exists with `LinkedInJobScraperTool(Tool)` registered
in the tool registry singleton, `tool_registry.list_ids()` returns both
`"website_scraper"` and `"linkedin_job_scraper"`, the tool's dry-run mode returns
a structured job signal dict from fixture data, and all 117 tests still pass.

### Acceptance criteria
- [ ] `tools/linkedin_job_scraper.py` exists with `LinkedInJobScraperTool(Tool)`:
  - `tool_id = "linkedin_job_scraper"`
  - `run(input_data: dict) -> dict | AgentError` accepts `{"company_name": str,
    "dry_run": bool}` — dry_run defaults to True
  - In dry-run mode: returns structured job signal dict from
    `tests/fixtures/sample_linkedin_jobs.json` without any HTTP calls
  - In live mode: returns `AgentError` with message
    `"LinkedIn live fetch not yet approved — dry-run only"` and does not attempt
    any HTTP call (live integration deferred to Sprint 7)
- [ ] `tests/fixtures/sample_linkedin_jobs.json` exists with mock job posting data:
  at least 3 job postings, each with `title`, `team`, `tech_stack_mentions` (list),
  and `seniority_level` fields
- [ ] Tool is pre-registered in the `orchestrator/tool_registry.py` singleton alongside
  `WebsiteScraperTool` — both registered on module import
- [ ] `orchestrator/tool_registry.py` updated: import of `LinkedInJobScraperTool`
  added; `registry.register(LinkedInJobScraperTool())` added below existing registration
- [ ] `tests/test_tool_registry.py` updated: adds tests for — `list_ids()` returns
  both tool IDs, `linkedin_job_scraper` dry-run returns dict with `job_postings` key,
  `linkedin_job_scraper` live mode returns `AgentError` without raising
- [ ] All 117 Sprint 5 tests still pass

### Execute with
Primary: backend
Collaborators: none
Reason: tools/linkedin_job_scraper.py, orchestrator/tool_registry.py, and
tests/test_tool_registry.py are all backend-owned Python files.

### Files to create/modify
- `tools/linkedin_job_scraper.py` — new file: LinkedInJobScraperTool class
- `tests/fixtures/sample_linkedin_jobs.json` — new file: mock job posting fixture
- `orchestrator/tool_registry.py` — add import and registration of LinkedInJobScraperTool
- `tests/test_tool_registry.py` — add tests for new tool registration and behavior

### Test certification required
yes

### Decision required
no (the decision to defer live LinkedIn fetch to Sprint 7 is a scope decision, not
an architecture decision — no ADR required)

### Blocked by
DISC-53 (scraper pattern must be stable before adding second tool)

---

## DISC-56: Low-Signal Confidence Warning Banner

**Owner:** Frontend
**Priority:** P2
**Blocked by:** DISC-53 (needs `signal_count` field in the POST /v1/analyze response,
which DISC-53 adds when it maps `pages_fetched` and `signal_count` to the API response)

### User story
As Sai using the system on a client with a thin web presence, I need a visible yellow
warning banner when the scraper extracted fewer than 3 signals so that I know the
analysis confidence is low before presenting it to the client — not after.

### done_when
After any analysis run where the API response contains `signal_count < 3`, a yellow
warning banner appears below the URL input field with the message "Low signal
confidence — only {n} signal(s) extracted. Analysis may be incomplete. Try submitting
a more detailed company URL." The banner is absent when `signal_count >= 3`.

### Acceptance criteria
- [ ] `frontend/app/components/ConfidenceWarning.tsx` exists:
  - Props: `signalCount: number`
  - Renders nothing when `signalCount >= 3`
  - Renders a yellow banner with warning text and signal count when `signalCount < 3`
  - Banner uses Tailwind classes consistent with neomorphic design system:
    `bg-yellow-50 border border-yellow-300 text-yellow-800 rounded-lg p-4`
  - Includes an icon (warning triangle — use a simple SVG inline, no external icon lib)
  - Warning text: "Low signal confidence — only {signalCount} signal(s) extracted.
    Analysis may be incomplete."
- [ ] `frontend/app/page.tsx` updated: renders `ConfidenceWarning` below the form
  and above the report sections, passing `signal_count` from the analyze API response
- [ ] `frontend/app/page.tsx` updated: TypeScript type for the analyze API response
  extended to include `signal_count: number` (alongside existing response fields)
- [ ] ConfidenceWarning is not rendered on initial page load (before any submit)
- [ ] ConfidenceWarning is not rendered during the loading state (while the API call
  is in flight — show loading spinner instead)
- [ ] No TypeScript errors on build (`npm run build` exits 0)
- [ ] `frontend/stories/ConfidenceWarning.stories.tsx` exists with two stories:
  - `LowSignal`: signalCount=2 → banner visible
  - `AdequateSignal`: signalCount=5 → nothing rendered
  — Sai can verify the component in Storybook without running the backend

### Execute with
Primary: frontend
Collaborators: none
Reason: ConfidenceWarning.tsx, page.tsx, and stories files are all frontend-owned
TypeScript files. The signal_count field in the API response is delivered by DISC-53
(backend) — frontend only reads it.

### Files to create/modify
- `frontend/app/components/ConfidenceWarning.tsx` — new component
- `frontend/app/page.tsx` — render ConfidenceWarning, extend response type
- `frontend/stories/ConfidenceWarning.stories.tsx` — new Storybook story

### Test certification required
yes (Storybook story renders without TypeScript error — visual certification; no
Playwright E2E tests in scope for Sprint 6)

### Decision required
no

### Blocked by
DISC-53 (signal_count field must be present in API response before frontend reads it)

---

## DISC-57: Cloud Run Deploy

**Owner:** Backend
**Priority:** P1
**Blocked by:** DISC-52 (eval scores must be real before deploy), DISC-54 (SLA must
be confirmed before deploy)

**TIER 3 CONDITION:** Sai must post an explicit "approved" comment on this ticket
before the backend agent executes any deploy step. PM blocks all deploy work until
that comment is received.

### User story
As Sai presenting to Tenex interviewers, I need a live Cloud Run URL so that I can
demonstrate the system from any machine without asking the interviewer to run
localhost commands or wait for a local server to start.

### done_when
The system is deployed to Cloud Run under the GCP project `plotpointe`, the URL
returns HTTP 200 on `GET /health`, `POST /v1/analyze` with a valid URL returns a
complete report, and the deploy URL is documented in `docs/SYSTEM_STATE.md` and
`README.md`.

### Acceptance criteria
- [ ] `Dockerfile` exists at repo root:
  - Base image: `python:3.11-slim`
  - Installs `requirements.txt`
  - Copies all source files except `.env`, `logs/`, `rag/store/`, `node_modules/`
  - Sets `PORT` env var and starts uvicorn: `CMD uvicorn infra.app:app --host 0.0.0.0 --port $PORT`
  - Image builds successfully with `docker build .`
- [ ] `infra/gcp_target.py` updated: `deploy()` method builds and pushes the Docker
  image to `gcr.io/plotpointe/ai-transform-agent:latest` and deploys to Cloud Run
  with: `--region us-central1`, `--memory 2Gi`, `--cpu 1`, `--min-instances 0`,
  `--max-instances 3`, `--allow-unauthenticated`
- [ ] All secrets injected via `--set-secrets` flag in the Cloud Run deploy command:
  `ANTHROPIC_API_KEY`, `VERTEX_MODEL`, `GCP_PROJECT_ID` — sourced from GCP Secret
  Manager (per ADR-005); no secrets hardcoded in Dockerfile or source
- [ ] `GET /health` on the deployed URL returns:
  ```json
  { "status": "ok", "version": "sprint6", "pipeline": "ready" }
  ```
- [ ] `POST /v1/analyze` on the deployed URL with `{"url": "https://example.com"}`
  (dry-run fixture) returns a non-error response within 90 seconds
- [ ] `.dockerignore` exists and excludes: `.env`, `logs/`, `rag/store/`, `.git/`,
  `node_modules/`, `__pycache__/`, `*.pyc`
- [ ] `infra/health_check.py` updated: `GET /health` response includes
  `"version": "sprint6"` so deploy can be verified by reading the version field
- [ ] `.github/workflows/llmops_gate.yml` updated: adds a smoke test step that calls
  `GET /health` on the Cloud Run URL after deploy and fails the workflow if the
  response is not 200
- [ ] `docs/SYSTEM_STATE.md` updated: Cloud Run URL added to "How to Start the System"
  section; deploy status set to "Live"
- [ ] `README.md` updated: live demo URL added to the top of the file
- [ ] All 117 Sprint 5 tests still pass (run against localhost, not Cloud Run)

### Execute with
Primary: backend
Collaborators: qa (QA updates `.github/workflows/llmops_gate.yml` with smoke test)
Reason: Dockerfile, infra/gcp_target.py, and infra/health_check.py are backend-owned
Python and config files. The CI smoke test workflow is QA-owned — QA runs as
collaborator after backend confirms the deploy URL.

### Files to create/modify
- `Dockerfile` — new file: production container definition
- `.dockerignore` — new file: excludes secrets, logs, and build artifacts
- `infra/gcp_target.py` — update deploy() method for Cloud Run
- `infra/health_check.py` — add version field to /health response
- `docs/SYSTEM_STATE.md` — add Cloud Run URL and update deploy status
- `README.md` — add live demo URL
- `.github/workflows/llmops_gate.yml` — add post-deploy smoke test (QA collaborator)

### Test certification required
yes — output comment must include: the live Cloud Run URL, result of
`curl <url>/health`, and `pytest tests/ -q --tb=short` passing count

### Decision required
yes — ADR-009 already reserved for DISC-54. This ticket files ADR-010:
"Cloud Run as production deploy target with zero-secrets-in-image policy" —
documents the deploy architecture, secret injection strategy, and why
`--allow-unauthenticated` is acceptable for MVP per ADR-002 scope.

### Blocked by
DISC-52 (real eval scores confirm quality before deploy),
DISC-54 (parallel writes confirm 90s SLA before deploy),
Sai approval (Tier 3 — explicit "approved" comment required on this ticket)

---

## Cross-Ticket Notes

### The signal_count API field dependency
DISC-56 (Frontend) reads `signal_count` from the POST /v1/analyze response. This
field is added by DISC-53 (Backend) when it maps `pages_fetched` and `signal_count`
into the API response body in `infra/app.py`. Frontend must not start DISC-56 until
DISC-53 is merged and the field is confirmed present. PM confirms this before spawning
the frontend agent.

### The ADR numbering
- ADR-009: Parallel report section writes (filed in DISC-54)
- ADR-010: Cloud Run deploy architecture (filed in DISC-57)
Both must be appended to `docs/decisions/INDEX.md` before their tickets close.

### The Tier 3 deploy gate
DISC-57 is blocked by Sai's explicit approval. PM opens the DISC-57 ticket on day 1
of Wave 3 and posts an escalation comment tagging Sai. The backend agent does NOT
start DISC-57 until that comment is received. If approval is not received within
48 hours of the ticket being opened, PM closes the sprint without the deploy ticket
and carries DISC-57 to Sprint 7 as P1.

### Fixture protection in DISC-53 and DISC-55
DISC-53 modifies `tests/fixtures/sample_company.json` (adds `products_page_content`).
DISC-55 creates `tests/fixtures/sample_linkedin_jobs.json` (new fixture).
Per CLAUDE.md fixture protection rules, DISC-53 is PM-approved (this ticket file
serves as the approval). All tests using `sample_company.json` must be re-run after
DISC-53 merges — confirmed via the "all 117 tests still pass" AC on every ticket.

### Eval scores and the quality floor
If DISC-52 produces any dimension average below 3.8, PM does NOT close Sprint 6
automatically. PM posts a Tier 2 escalation to Sai with: the failing dimension name,
the actual score, and a recommendation (either accept the score as Sprint 6 floor
and schedule a prompt engineering ticket for Sprint 7, or block sprint close until
a PE fix is applied). Sai decides.

---

## Sprint 6 Definition of Done

- [ ] `pytest tests/ -q --tb=short` passes — all 117 Sprint 5 tests plus new Sprint 6
  tests green
- [ ] `evals/baselines.json` has a `sprint_6` key with real judge scores (not 0.0)
- [ ] `python orchestrator/pipeline.py --dry-run` completes in under 30 seconds
  (parallel writes must show measurable improvement)
- [ ] Scraper fetches >= 3 candidate pages per domain in dry-run (confirmed in test)
- [ ] `curl <cloud-run-url>/health` returns 200 with `"version": "sprint6"`
- [ ] Low-signal warning banner visible in Storybook with signalCount=2
- [ ] `orchestrator/tool_registry.py` lists both tool IDs when `list_ids()` is called
- [ ] ADR-009 and ADR-010 both filed in `docs/decisions/` and indexed in INDEX.md
- [ ] QA sign-off comment posted with: test count, eval scores, deploy URL,
  dry-run timing (before and after parallel writes), and Sai test instructions
