# Sprint Roadmap — AI Transformation Discovery Agent

> Last updated: 2026-03-16 by PM  
> Scope: Sprint 4 onward. Sprints 0-3 are history.  
> Rule: every sprint ends with something Sai can open in a browser and test.

---

## Sprint 4 — "See the Report"

**Goal:** Ship the full three-tier report visible in the browser — green/amber/blue cards,
dimension bars, evidence panels, data flow descriptions. Not JSON. The actual report.

**What Sai sees:** Opens a URL, types in a company domain, waits 90 seconds, sees a
three-panel report with tier-colored use case cards and a maturity score bar chart.
Every claim cites a raw quote from the company's website.

### Tickets

| # | Owner | What | Priority |
|---|-------|------|----------|
| DISC-39 | Backend | Pydantic schemas + validators in `orchestrator/schemas.py` | P1 — blocks everything |
| DISC-40 | Backend | SignalExtractorAgent + scraper expansion (product/solutions/features pages) + graceful degradation for thin-signal companies | P1 |
| DISC-41 | Backend | MaturityScorerAgent + VictoryMatcherAgent (combined — victory matching is deterministic logic, not a model call) | P1 |
| DISC-42 | Backend | UseCaseGeneratorAgent + orchestrator pipeline wiring (7-stage chain, parallel report writer sections) | P1 |
| DISC-43 | PM | Four prompts: `signal_extractor.md`, `maturity_scorer.md`, `victory_matcher.md`, `use_case_generator.md` | P1 — write in parallel with DISC-39 |
| DISC-44 | Frontend | Three-tier report UI: tier-colored cards (green/amber/blue), dimension score bars, evidence panel, data flow section | P1 |
| DISC-45 | QA | Fixtures for all new agents + dry-run end-to-end + 55-test baseline preserved | P1 |

### Key decisions

- Tool registry deferred to Sprint 5. Sprint 4 has one tool — no registry needed yet.
- VictoryMatcher is deterministic scoring in the orchestrator, not a separate model call. Saves one LLM hop.
- Scraper expands to fetch `/product`, `/solutions`, `/features` pages. Costs 10 lines, meaningfully raises signal density.
- Thin-signal path: if signal count < 3, pipeline continues with `confidence: LOW` flag visible in UI. Never aborts.
- Report writer sections run in parallel (5 async flash calls). Required to stay under 90-second SLA.
- PM delivers all four prompts before backend starts DISC-42 (use case generator).

### Done when

- `python orchestrator/pipeline.py --dry-run` completes with three-tier structured output
- Sai opens the browser, submits a real company URL, sees a rendered three-tier report
- All 55+ tests pass
- Report renders in under 90 seconds on a live run

---

## Sprint 5 — "Trust the Report"

**Goal:** Understand and measure what the pipeline is actually doing. Tracing at every
step. Calibrated victories. Eval scores across five real companies.

**What Sai sees:** After running a report, opens a trace view (log or simple dashboard)
and sees exactly what each agent received and produced. Eval scores for five companies
show where the system is strong and where it needs work.

### Tickets

| # | Owner | What | Priority |
|---|-------|------|----------|
| DISC-46 | Backend | Input/output logging at every agent stage via `ops/logger.py` — what each agent saw, what it returned, latency, model used | P1 |
| DISC-47 | Backend | Victory calibration: add `industry_benchmark`, `success_threshold`, `gap_analysis` fields to victories.json. Update VictoryMatcher to surface gap. | P1 |
| DISC-48 | Backend | Tool registry abstraction (`Tool` ABC, `ToolRegistry`) — now we're adding a second tool, so the registry earns its weight | P2 |
| DISC-49 | QA | Eval rubrics for three-tier output (tier classification accuracy, evidence grounding, ROI basis) + baseline run across 5 test companies | P1 |
| DISC-50 | Frontend | Trace panel in UI: collapsible per-stage view showing agent inputs/outputs for any run | P2 |
| DISC-51 | PM | Update victories.json with calibration fields (20 victories with benchmarks, thresholds, gap analysis) | P1 |

### Key decisions

- Trace view is a collapsible panel in the existing UI, not a separate page. Keeps scope tight.
- Victory calibration populates the use case generator's ROI grounding. PM owns the data, not Backend.
- Eval rubrics target three dimensions: tier classification accuracy, evidence citation rate, ROI number traceability.
- Eval baseline established this sprint. Sprint 6 cannot regress below it.

### Done when

- Every pipeline run writes a JSONL trace to `logs/runs/{run_id}.jsonl`
- UI trace panel shows per-stage inputs and outputs
- Eval baseline scores recorded in `evals/baselines.json` for 5 test companies
- Victories have calibration fields; use case generator cites gap analysis in output

---

## Sprint 6 — "Better Signals"

**Goal:** More data sources, richer signals, more victories. The core loop works —
now make the inputs better.

**What Sai sees:** Submits a Fortune 500 URL that previously produced thin signals.
Now gets a richer report because the system fetched job board data and recent news.
Eval scores improve vs Sprint 5 baseline.

### Tickets

| # | Owner | What | Priority |
|---|-------|------|----------|
| DISC-52 | Backend | Job board tool: fetch job listings from Greenhouse/Lever embed URLs or LinkedIn company jobs page | P1 |
| DISC-53 | Backend | News search tool: fetch recent company news (funding, product launches, AI mentions) via a search API | P2 |
| DISC-54 | Backend | Signal ranker: deduplicate + rank signals by type coverage; enforce budget of top 30 before passing to MaturityScorer | P1 |
| DISC-55 | PM | Expand victories.json to 30-50 wins with calibration data across 8+ industries | P1 |
| DISC-56 | QA | Re-run evals on 5 test companies with new tools active; regression check vs Sprint 5 baseline | P1 |

### Key decisions

- Two tools now live in the registry. Tool registry from Sprint 5 earns its cost here.
- Signal budget enforced at 30 ranked signals. Above this, the maturity scorer context window bloats.
- News tool is P2 — if job board tool alone raises eval scores above baseline, news tool slips to Sprint 7.
- Victory expansion targets underrepresented industries first (healthcare, manufacturing, logistics).

### Done when

- Pipeline runs on a company with ATS-redirect careers page and produces 8+ signals
- Eval scores for 5 test companies meet or exceed Sprint 5 baseline
- 30+ calibrated victories in victories.json

---

## Sprint 7 — "Demo Ready"

**Goal:** Polish, export, streaming, and Tenex branding. The system is functionally
complete — Sprint 7 makes it presentable for the submission deadline.

**What Sai sees:** A demo-quality product. Clean branding, PDF download, a streaming
progress bar that counts down the 90 seconds, share links that work.

### Tickets

| # | Owner | What | Priority |
|---|-------|------|----------|
| DISC-57 | Backend | SSE streaming: emit progress events per pipeline stage so the UI can show a live progress bar | P1 |
| DISC-58 | Frontend | Progress bar component: shows each stage completing in real time during the 90-second run | P1 |
| DISC-59 | Frontend | PDF export: "Download Report" button generates a clean single-page PDF | P2 |
| DISC-60 | Frontend | Share link: unique URL per report that renders the cached result | P2 |
| DISC-61 | Frontend | Tenex branding pass: logo, color palette, typography, demo URL | P1 |
| DISC-62 | QA | Load test: 5 concurrent runs, verify < 90s SLA holds, no OOM on Cloud Run | P1 |
| DISC-63 | PM | Demo rehearsal doc: step-by-step demo script, 5 backup company URLs tested, known-good outputs archived | P1 |

### Key decisions

- Follow-up Q&A deferred post-submission. It is a feature, not a demo requirement.
- PDF uses browser print CSS, not a headless Chrome dependency. Keeps infrastructure simple.
- Share link caches report JSON in Cloud Storage (one file per run_id). No database.
- Load test runs from QA before Sai approves deploy ticket. Deploy ticket is a Tier 3 gate.

### Done when

- Sai runs the demo script end-to-end in under 90 seconds on a real company URL
- PDF downloads cleanly
- Progress bar shows live stage updates
- Load test passes at 5 concurrent users
- Sai posts "approved" on the deploy ticket
- `git tag v1.0.0` created on main

---

## Sprint Dependency Summary

```
Sprint 4 → Sprint 5 → Sprint 6 → Sprint 7
  |           |           |           |
  Report      Tracing     Signals     Polish
  visible     + evals     + sources   + deploy
```

No sprint starts until the prior sprint's "Done when" criteria are met and Sai has
tested the visible deliverable.

---

## What We Are NOT Building (Explicit Deferrals)

| Feature | Reason | When |
|---------|--------|------|
| Follow-up Q&A chat | Requires session state, not a demo blocker | Post-submission |
| Auth / login | ADR-002 locked — no auth for MVP | Day-2 toggle |
| Multi-company comparison | Complicates UI, not requested | Post-submission |
| Custom scoring weights | Adds UI complexity, low demo value | Post-submission |
| Webhook / async notify | Only needed at high volume | Post-submission |
