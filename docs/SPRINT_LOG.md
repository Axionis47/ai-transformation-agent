# Sprint Log

What happened each sprint. What shipped, what didn't, and why.

---

## Sprint 7 - Documentation

Date: March 2026
Goal: Full codebase scan and documentation rebuild. Ensure every doc reflects what is
actually in the code, not what was planned.

### Shipped

- DISC-64: COMPONENT_MAP.md - every file documented with its role and dependencies
- DISC-65: CONTRACTS.md - all interface contracts from actual code, not spec
- DISC-66: ARCHITECTURE.md rebuilt from code - Mermaid diagrams, layer boundaries
- DISC-67: WIREFRAMES.md rebuilt from code - screens, user flow, routing, design system
- DISC-68: SYSTEM_STATE.md verified against code - what works, what is blocked, how to test
- DISC-69: SPRINT_LOG.md (this file)

Also shipped during Sprint 7 execution as part of related front-end work (on branch
fe/DISC-65-nav-page-structure):
- Analysis results page at /analysis/[runId]
- ResultsView component extracted from AnalyzeForm
- Sticky section navigation bar in report view
- Home link in header and footer
- Page fade-in animation

### Metrics

| Tests | Eval Scores | Cost/Run |
|-------|-------------|----------|
| 140+ (no regressions) | sprint_6 floor: tier 3.67, evidence 3.20, roi 3.07 | ~$0.01 |

### Key Decisions

No new ADRs this sprint. Documentation sprint only.

### What Carried Forward

- DISC-55 LinkedInJobScraper (carried from Sprint 6)
- Live Cloud Run deploy requires Sai approval (Tier 3 gate)
- Eval scores below 3.8 threshold - prompt engineering work remains

---

## Sprint 7 (Execution Sprint) - CI/CD and Quality

Date: March 2026
Goal: Automated CI/CD on every push, eval scores >= 3.8, live Cloud Run URL.

Note: Ticket numbers overlap with the documentation sprint above because the sprint
was replanned mid-cycle. The execution sprint here refers to the tickets in
sprint7_plan.md (DISC-58 through DISC-63).

### Shipped

- DISC-58: GitHub Actions CI pipeline - pytest, ruff lint, eval regression gate on every push
- DISC-59: Cloud Run CD pipeline - builds, pushes to gcr.io, deploys to Cloud Run on main merge
- DISC-60: Prompt engineering - report_writer.md and use_case_generator.md updated for evidence grounding
- DISC-61: GCP defaults hardcoded - `python orchestrator/pipeline.py --dry-run` works with zero env setup
- DISC-62: Low-signal warning banner - yellow banner when signal_count < 3

### Cut

- DISC-63: Production deploy - carried. Tier 3 gate. Sai must post approval on ticket before execution.
- DISC-55: LinkedInJobScraper - carried again from Sprint 6.

### Metrics

| Tests | Eval Scores | Cost/Run |
|-------|-------------|----------|
| 140+ | sprint_7 target: all dims >= 3.8 (sprint_6 floor: 3.07-3.67) | ~$0.01 |

### Key Decisions

No new ADRs filed. ADR-009 and ADR-010 from Sprint 6 cover the relevant architecture.

---

## Sprint 6 - Ship It

Date: March 2026
Goal: Close the gap between prototype and Tenex-submission-ready product. Real eval scores,
richer signals from product pages, parallel report writes, Docker and Cloud Run deploy.

### Shipped

- DISC-52: Real eval baseline run - baselines.json sprint_6 key populated with Gemini judge scores
  (eval judge switched from Anthropic to Gemini on Vertex AI due to quota issues)
- DISC-53: Extended scraper - fetches /products, /solutions, /platform in addition to /about and /careers;
  pages_fetched and signal_count added to API response
- DISC-54: Parallel report section writes - ThreadPoolExecutor(max_workers=3) replaces sequential calls;
  per-section failure isolation added
- DISC-57: Cloud Run deploy prep - Dockerfile at repo root, infra/gcp_target.py implemented, health check
  endpoint with version field. Sai approved. Deploy prep complete. Live execution blocked on GCP-authenticated
  shell.

### Cut

- DISC-55: LinkedInJobScraper - cut to Sprint 7 (second carry)
- DISC-56: Low-signal warning banner - cut to Sprint 7

### Metrics

| Tests | Eval Scores | Cost/Run |
|-------|-------------|----------|
| 140 (up from 117) | tier_classification: 3.67, evidence_grounding: 3.20, roi_basis: 3.07 | ~$0.01 |

Sprint 5 eval scores were all 0.0 (ANTHROPIC_API_KEY not set). Sprint 6 established the first real
baseline using Gemini 2.5 Pro on Vertex AI as the judge. All three dimensions below 3.8 threshold.

### Key Decisions

- ADR-009: Parallel report section writes via ThreadPoolExecutor with semaphore(3) concurrency cap
- ADR-010: Cloud Run as production deploy target with zero-secrets-in-image policy

### What Carried Forward

- Real eval scores below 3.8 - prompt engineering target for Sprint 7
- LinkedInJobScraper (DISC-55) - carried for third time
- Live Cloud Run URL - deploy prep done; execution requires GCP credentials and Sai Tier 3 approval

---

## Sprint 5 - Trust the Report

Date: March 2026
Goal: Per-stage observability into the pipeline, calibrated victories with gap analysis, eval
baseline across 5 test companies.

### Shipped

- DISC-46: Per-stage I/O logging - ops/logger.py enhanced with log_agent_call() method;
  every pipeline stage logs input_summary and output_summary to JSONL
- DISC-47: Victory calibration and gap analysis - VictoryMatcher computes gap between company
  composite score and victory maturity_at_engagement; gap_analysis surfaced in VictoryMatch output
- DISC-48: Tool registry abstraction - Tool ABC, ToolRegistry class, WebsiteScraperTool registered
  as first tool; pipeline retrieves scraper via registry
- DISC-49: Eval rubrics, judge client, and baseline run - three rubric YAML files (tier_classification,
  evidence_grounding, roi_basis), JudgeClient class, ci_eval.py, baselines.json structure created.
  Scores all 0.0 because ANTHROPIC_API_KEY was not set in the QA environment.
- DISC-50: Trace panel in UI - TracePanel and TraceStageRow components, collapsible per-stage view,
  GET /v1/trace/{run_id} endpoint
- DISC-51: victories.json calibration fields - 20 victories updated with industry_benchmark,
  success_threshold, and gap_analysis_template fields

### Cut

Nothing cut this sprint. All 6 tickets shipped.

### Metrics

| Tests | Eval Scores | Cost/Run |
|-------|-------------|----------|
| 117 (up from 79) | 0.0 (ANTHROPIC_API_KEY not set) | ~$0.01 |

The eval framework was built and the baseline structure was created. Real scores were blocked
by missing API credentials. This was escalated as a Tier 2 issue.

### Key Decisions

- ADR-008: Tool Registry as orchestrator-level abstraction - documents why registry lives in
  orchestrator/ and why Tool.run() returns dict|AgentError rather than raising

### What Carried Forward

- Real eval scores - DISC-52 in Sprint 6 resolved this by switching judge to Gemini on Vertex AI
- Low-signal warning banner - deferred to Sprint 6 (DISC-56 in Sprint 6 tickets)

---

## Sprint 4 - See the Report

Date: March 2026
Goal: Ship the full three-tier report visible in the browser. Green, amber, and blue use case cards.
Dimension score bars. Evidence panels. The actual rendered report, not JSON.

### Shipped

- DISC-50: Pydantic schemas and validators - orchestrator/schemas.py with Signal, SignalSet,
  MaturityResult, VictoryMatch, DataFlow, UseCase models; orchestrator/validators.py with
  validate_signal_set, validate_maturity, validate_victories, validate_use_cases, validate_report
- DISC-51: Four agent prompts - prompts/signal_extractor.md, prompts/maturity_scorer.md,
  prompts/use_case_generator.md created at v1.0; prompts/consultant.md marked as superseded
- DISC-52: Scraper expansion plus SignalExtractorAgent - scraper fetches product, solutions, and
  features pages in addition to about and careers; SignalExtractorAgent converts raw text to
  validated SignalSet
- DISC-53: MaturityScorerAgent plus deterministic VictoryMatcher - MaturityScorerAgent scores
  four dimensions; VictoryMatcher is pure Python scoring with no model call; three-tier classification
  (DIRECT_MATCH, CALIBRATION_MATCH, ADJACENT_MATCH)
- DISC-54: UseCaseGeneratorAgent plus pipeline rewire - 7-stage pipeline replaces 4-stage chain;
  context scoping for report writer; orchestrator/state.py gains signal_set, maturity, victory_matches,
  use_cases fields
- DISC-55: Three-tier report UI - UseCaseCard with tier-color borders, DimensionBar, MaturityPanel,
  EvidencePanel, ConfidenceBanner; page layout with tier-colored cards and expandable data flow sections
- DISC-56: Fixtures, dry-run, regression baseline - sample_signals.json, sample_maturity.json,
  sample_victories.json, sample_use_cases.json; test_pipeline_e2e.py; regression_log.md updated with
  Sprint 4 baseline at 79 tests

### Cut

Nothing cut this sprint. All 7 tickets shipped.

### Metrics

| Tests | Eval Scores | Cost/Run |
|-------|-------------|----------|
| 79 (up from ~30 at Sprint 3) | Not yet established | ~$0.01 |

### Key Decisions

- VictoryMatcher is deterministic Python, not a model call. Saves one LLM hop per run.
- Tool registry deferred to Sprint 5. With one tool, the registry added no value.
- Thin-signal path: if signal_count < 3, pipeline continues with confidence=LOW rather than aborting.
  The Sprint 4 review (sprint4_review.md) flagged that 40-60% of real company URLs would produce
  thin signals if the pipeline aborted on < 3 signals.

### What Carried Forward

- Tool registry - shipped in Sprint 5 (DISC-48)
- Product/solutions page scraping - shipped as part of DISC-52

---

## Sprint 3 - Victory Data as the Backbone

Date: March 2026
Goal: Make the RAG system cite Tenex wins, not generic benchmarks. A logistics company URL
should produce a report that says "based on win-001 (route optimization for a mid-market
logistics carrier), we achieved 14% fuel cost reduction."

The pivot: Tenex's actual delivery track record (20 real wins in victories.json) replaced
the generic seeds.json. The question shifted from "can the system produce a report" to
"does the report cite things a CFO would believe."

### Shipped

- DISC-30: Victory data ingest and RAG query alignment - rag/ingest.py updated to load
  victories.json using embed_text field; rag_query.py builds structured query from company data
- DISC-31: Consultant prompt v2 with victory citation - prompts/consultant.md updated to v2.0;
  agents/consultant.py formats RAG context as structured win summaries; format_wins helper added
- DISC-32: Evidence panel with victory wins in UI - EvidencePanel.tsx component added with
  collapsible drawer; VictoryMatch types added; MaturityBadge updated with dimension bars
- DISC-33: Scraper content quality gate - orchestrator/gates.py with scraper_quality_gate();
  gate integrated into pipeline; API returns 422 with SCRAPE_THIN on gate failure
- DISC-34: Sprint 3 eval baseline - victory_citation rubric created; baseline structure established

### Cut

Nothing explicitly cut from the Sprint 3 scope.

### Metrics

| Tests | Eval Scores | Cost/Run |
|-------|-------------|----------|
| ~30 (Sprint 2 baseline before S3 additions) | Not yet established | ~$0.009 |

No cost increase from Sprint 2. The victory integration was a prompt and data change, not
additional model calls.

### Key Decisions

- ADR-007: Victory Data Schema and RAG Seed Strategy - victories.json as primary RAG source;
  embed_text field is the sole embedded document per victory record; seeds.json deprecated

### What Carried Forward

- Signal extractor agent - deferred to Sprint 4
- Focus area context input - deferred
- PDF export - deferred
- The core problem: 40-60% of companies have thin websites. Sprint 4 reviewed this in depth
  (sprint4_review.md) and the VictoryMatcher architecture addressed it.

---

## Sprint 2 - Live Pipeline and Frontend

Date: March 2026
Goal: Get the pipeline running end-to-end on a real URL and render it in a browser.

Sprint 1 scaffolded the project. Sprint 2 was the first sprint where Sai could open a URL
and see something.

No spec files for Sprints 1-2 exist in docs/specs/. The following is reconstructed from
git history.

### What git history shows was built in Sprint 2

From commits between Sprint 1 scaffold and Sprint 3 work:

Backend:
- Structured JSONL logger (ops/logger.py) with per-stage logging
- Per-stage timeouts and cost tracking in pipeline.py
- API analysis field included in response
- Model client JSON config and code fence stripping for Vertex responses
- Dockerfiles for backend and frontend (Cloud Run deployment)
- FastAPI entry point at POST /v1/analyze

Frontend:
- Next.js 14 project with TypeScript and Tailwind
- App shell with neomorphic design tokens
- TypeScript types and report display components
- URL input form and pipeline state display
- AnalyzeForm orchestrator wiring main page
- Storybook configuration and component stories

### Sprint 2 state at close

Per sprint3_plan.md "Currently working" section:
- Live backend: https://ai-transform-agent-359145045403.us-central1.run.app
- Live frontend: https://ai-transform-frontend-359145045403.us-central1.run.app
- Pipeline: Scraper -> RAG -> Consultant -> Report Writer (4 stages, linear)
- 30 tests passing
- seeds.json (10 generic text-blob seeds) ingested into ChromaDB

### Key Decisions

- ADRs 001-006 all filed on 2026-03-14:
  - ADR-001: Infrastructure Stack for MVP (Cloud Run, FastAPI, ChromaDB, Next.js)
  - ADR-002: Authentication Strategy (no auth for MVP)
  - ADR-003: Vector Store Selection (ChromaDB)
  - ADR-004: Model Routing Configuration (Vertex AI primary, Ollama fallback)
  - ADR-005: Secrets Management (GCP Secret Manager)
  - ADR-006: Analysis Specification v1.0 (maturity scoring framework)

---

## Sprint 1 - Project Scaffold

Date: March 2026
Goal: Get the project structure, abstractions, and CI hooks in place. Establish the
agent contracts and file ownership before writing any real pipeline logic.

No spec files for Sprint 1 exist in docs/specs/. The following is from git history.

### What was built

From the earliest commits:
- Project directory structure and .gitignore
- requirements.txt with pinned dependencies (numpy compat fix for chromadb included)
- Architecture diagrams, SYSTEM_STATE.md, and ADR decisions (ADRs 001-005)
- Deploy target abstraction (infra/deploy_target.py) and health check endpoint
- Agent contract (base.py with AgentError), model client abstraction (ops/model_client.py),
  vector store abstraction (rag/vector_store.py)
- Dry-run fixtures for end-to-end pipeline testing
- Scraper, RAG query, consultant, and report writer stubs
- Orchestrator pipeline with dry-run end-to-end mode
- Infrastructure critique docs from sprint planning review
- FastAPI entry point with POST /v1/analyze endpoint
- Async endpoint tests with dry-run and failure coverage
- Consultant prompt v1.0 with maturity scoring framework
- Report writer prompt with section audience rules and ROI/roadmap rules
- prompts/VERSIONS.md
- RAG seed ingest script with upsert support and tests

### Key outcome

At Sprint 1 end: `python orchestrator/pipeline.py --dry-run` worked. The pipeline ran
against fixtures with no real API calls. Every abstraction layer existed. No live
endpoint yet.

---

## Summary Table

| Sprint | Theme | Tests | Eval Avg | Pipeline Stages | Key Milestone |
|--------|-------|-------|----------|-----------------|---------------|
| 1 | Scaffold | ~10 | - | 4 (stubs) | Dry-run works |
| 2 | Live Pipeline | ~30 | - | 4 (live) | Live on Cloud Run |
| 3 | Victory Data | ~30 | - | 4 | Reports cite win-NNN |
| 4 | See the Report | 79 | - | 7 | Tier-colored cards in browser |
| 5 | Trust the Report | 117 | 0.0* | 7 | Trace panel, eval framework |
| 6 | Ship It | 140 | 3.31 avg | 7 | Docker, parallel writes, real scores |
| 7 (CI/CD) | CI/CD & Quality | 140+ | target 3.8 | 7 | GitHub Actions CI/CD |
| 7 (Docs) | Documentation | 140+ | - | 7 | All docs rebuilt from code |

*Sprint 5 scores were 0.0 due to missing ANTHROPIC_API_KEY. Sprint 6 established the first
real baseline using Gemini 2.5 Pro on Vertex AI.

Sprint 6 averages: tier_classification=3.67, evidence_grounding=3.20, roi_basis=3.07.
All below the 3.8 threshold. Sprint 7 prompt engineering work targets this gap.
