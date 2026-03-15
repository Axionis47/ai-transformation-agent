# Infrastructure Critique — Sprint 1 Readiness Review

**Author:** DOC agent — Decision Council
**Sprint:** Pre-Sprint 1
**Purpose:** Flow critique and scope reduction before execution agents start building

---

## Context

The goal is a 90-second demo pipeline: URL in, 5-section report out.
Cost target is ~$0.01 per run. Audience is Tenex evaluators clicking a URL.

The critique below judges every planned component against that single test:
**Does this help a Tenex evaluator get a report in 90 seconds?**
If yes, keep it. If no, cut it or defer it.

---

## KEEP — These are load-bearing for Sprint 1

### The 5-step pipeline (scraper → consultant → RAG → report writer → render)
This is the entire product. Every agent and every file that serves this chain
is justified. The sequence must be unbreakable before anything else is added.

### ops/model_client.py with VertexProvider
The abstraction is correct and already decided (ADR-004). A single interface
that reads MODEL_PROVIDER from env and routes accordingly means provider swap
never touches agent code. Build this first.

### rag/vector_store.py with ChromaDB
20 seed solutions loaded in-process with no network hop is the right call for
Sprint 1 (ADR-003). The abstraction is already in place. Keep ChromaDB local
for development. GCS persistence is a Sprint 2 concern once the pipeline runs.

### agents/base.py with AgentError contract
Every agent must return typed output or AgentError. This is the error boundary
that prevents one bad scrape from crashing the whole pipeline. It must exist
before any agent is written.

### orchestrator/pipeline.py --dry-run mode
The dry-run with fixtures is the primary local testing tool. It must work with
zero real API calls. This is how every agent can be tested in isolation without
burning money. Keep and prioritize.

### infra/health_check.py
Already built and correct. Cloud Run needs /health. It's 30 lines and done.
No changes needed.

### .env.example and secrets pattern
Already handled (ADR-005). Workload Identity for GCP, Secret Manager for keys,
.env for local. This is complete.

---

## CUT — Sprint 1 does not need these

### infra/deploy_target.py — defer the implementation
The abstract interface exists and that is fine. But GCPCloudRunTarget.deploy()
raises NotImplementedError and that is exactly right — leave it that way for
Sprint 1.

The deploy workflow is: `gcloud run deploy --image` run once by Sai.
No agent needs to programmatically trigger deploys during Sprint 1.
The abstraction stays; the implementation waits until Sprint 2.

**Risk if we build it now:** Sprint 1 time spent on deploy automation when
the pipeline doesn't run yet. Deploy automation is useless without a working
pipeline.

### ops/trace_setup.py (Langfuse integration)
The env vars are documented in .env.example as optional. That is the right
status. Do not build trace_setup.py in Sprint 1.

Langfuse is observability tooling. You need something to observe before you
instrument it. Build the pipeline first, add tracing in Sprint 2 or 3 when
eval scores start moving and you need to debug prompt quality.

**Risk if we build it now:** LLMOps agent spends a sprint wiring Langfuse
before any model calls exist to trace.

### Cloud Build pipeline
ADR-001 lists Cloud Build for deploy. For Sprint 1, this is not needed.
GitHub Actions runs lint and tests. Sai manually deploys with a single
gcloud command. Cloud Build adds no value until there are multiple engineers
deploying multiple times per day.

**When to add it:** Sprint 3, when the pipeline is stable and QA needs
reproducible deploy verification.

### ops/budget_config.yaml with automated cost gates
Document the thresholds. Do not build automated circuit breakers yet.

The cost model is $0.011 per pipeline run. At that price, even 1000 accidental
runs cost $11. There is no cost emergency to automate against in Sprint 1.
Log the cost per run in JSONL. Check it manually. Add the gate in Sprint 2
once you know the real cost distribution from actual runs.

### Pinecone as a vector store option
The code currently has VECTOR_STORE=chroma|pinecone as an env var option.
Do not implement a PineconeVectorStore class in Sprint 1. The abstraction
already supports it as a future option. 20 seed documents do not need Pinecone.
Remove the option from the env var comment until it has an implementation
or it will confuse agents into thinking it works.

---

## ADD — Gaps that will break the pipeline without these

### A FastAPI app.py to wire the pipeline to an HTTP endpoint
The architecture diagram shows a POST /analyze endpoint but there is no
app.py file in the repo structure. Without this file, the frontend has nothing
to call and Cloud Run has nothing to serve.

This is the most critical missing piece. Sprint 1 must produce:
- `POST /analyze` accepting `{ "url": "https://..." }`
- Synchronous response with the full report JSON
- Returns 200 with report or 422 with structured AgentError

**Who builds it:** Backend agent, Sprint 1.

### A concrete timeout contract on each pipeline stage
The CLAUDE.md mentions 30-second timeout per section but no code enforces it.
If the scraper hangs on a slow site, the whole 90-second budget is gone.

Each agent call needs a timeout wrapper at the orchestrator level. The timeout
value should come from an env var, not be hardcoded. Without this, the first
demo on a slow company site will time out and the demo fails in front of
Tenex evaluators.

**Who builds it:** Backend agent, Sprint 1, in pipeline.py.

### Test fixtures before any agent code
The dry-run depends on fixtures. The fixtures do not exist yet. They must be
created before any agent is tested, or every test requires a live API call.

Required files:
- `tests/fixtures/sample_company.json` — a realistic scrape result
- `tests/fixtures/sample_analysis.json` — a realistic consultant output
- `tests/fixtures/sample_report.json` — a realistic report with all 5 sections
- `tests/fixtures/rag_seeds/seeds.json` — 20 seed solutions for the vector store

**Who builds it:** Backend agent creates the schemas; QA populates them with
realistic data. Sprint 1, before pipeline.py tests are written.

### GCS bucket and startup load for ChromaDB
ADR-003 says ChromaDB persists to Cloud Storage for production. The startup
sequence for loading from GCS is not defined anywhere in the current repo.

When Cloud Run starts a cold instance, it needs to:
1. Download the vector store from GCS
2. Load ChromaDB into memory
3. Signal ready (health check passes)

If step 3 completes before steps 1 and 2, the first request will fail with
an empty vector store. This is a broken flow that will silently produce
bad reports with zero RAG matches.

**Who builds it:** RAG agent, Sprint 1, in rag/vector_store.py startup logic.

---

## USE EXISTING SERVICE INSTEAD — Do not build these from scratch

### Authentication
Already decided correctly in ADR-002. No auth for MVP. Cloud IAP is the
day-2 toggle. Do not build login flows, session management, API keys, or
rate limiting middleware. Zero lines of auth code in Sprint 1.

If Tenex evaluators abuse the public URL, enable Cloud Armor. It is a GCP
checkbox, not a development task.

### CI/CD pipeline
GitHub Actions is already configured for lint and tests. That is sufficient
for Sprint 1.

Do not build a custom deploy pipeline. The deploy command is:
```
gcloud run deploy ai-transform-agent \
  --image gcr.io/PROJECT/ai-transform-agent:latest \
  --region us-central1
```

That is the entire deploy process. One command. Sai runs it. No pipeline
needed until Sprint 3.

### Monitoring dashboard
Cloud Run provides request latency, error rates, and instance count out of
the box in the GCP console. There is nothing to build. Do not create custom
dashboards, alerting policies, or uptime checks in Sprint 1.

The only monitoring that matters right now is: did the pipeline return a
non-null report? That is answered by the eval scores, not a dashboard.

### Container orchestration
Cloud Run handles this. No Kubernetes, no Docker Compose production configs,
no service mesh. The container image runs. Cloud Run scales it. Done.

### Secret rotation
Secret Manager handles this. Do not build rotation scripts or custom secret
versioning. The only agent interaction with secrets is reading them from env
vars, which Secret Manager mounts automatically on Cloud Run.

### Logging infrastructure
Cloud Run automatically ships stdout/stderr to Cloud Logging. The JSONL logs
in logs/runs/ are for local debugging only (and are gitignored). Do not build
a custom log aggregation pipeline, log parsing tools, or alerting on log
patterns. Cloud Logging already does this and is already enabled.

---

## Broken Flows — Where Users Will Struggle

### Flow 1: Scraper fails on bot-protected sites
Companies like Cloudflare-protected or JavaScript-heavy SPAs will return empty
or garbage content. The consultant then scores a company with no evidence.
The user gets a report that looks real but is fabricated.

There is no current validation that scraped content meets a minimum quality
bar before it reaches the consultant. This is not a Sprint 1 blocker if we
pick demo-friendly companies. It is a Sprint 2 problem.

**Recommendation:** In Sprint 1, add a simple check in the orchestrator:
if scraped content is under 200 characters total, return an error before
the consultant runs.

### Flow 2: ChromaDB empty at first request after cold start
Documented in the ADD section above. RAG returns zero matches. Report writer
generates sections with no comparable companies. The report looks thin.

This is a Sprint 1 blocker. The seed data must be in the container or loaded
before the first request is served.

### Flow 3: Report JSON structure mismatch between backend and frontend
The data flow in ARCHITECTURE.md shows ReportSections with five fields.
If the consultant returns a different field name, or the report writer returns
a list instead of a string, the frontend renderer will crash silently or
display nothing.

There is no schema validation contract between the pipeline output and the
frontend renderer. Pydantic models in PipelineState need to be the single
source of truth. The frontend TypeScript types must match them exactly.

**Who validates this:** QA, at every sprint boundary.

---

## Sprint 1 Priority Order (DOC Recommendation)

Based on what would break the demo and what is currently missing:

1. agents/base.py and AgentError — everything else depends on this
2. tests/fixtures/ — enables dry-run without API calls
3. ops/model_client.py with VertexProvider — enables consultant and report writer
4. agents/scraper.py with timeout and minimum content validation
5. agents/consultant.py with maturity scoring
6. rag/vector_store.py with ChromaDB + seed data loaded at startup
7. agents/report_writer.py generating all 5 sections
8. orchestrator/pipeline.py wiring all agents with per-stage timeouts
9. app.py exposing POST /analyze
10. One frontend component that renders the report JSON

Do not start item 9 or 10 until item 8 passes dry-run. The pipeline must be
demonstrably working before frontend tickets are opened.

---

## What Sai Can Test at Sprint 1 End

If the above is built in order:

```
pytest tests/ -q --tb=short
  → all tests green

python orchestrator/pipeline.py --dry-run
  → returns full 5-section report from fixtures, no API calls

curl -X POST http://localhost:8000/analyze \
  -d '{"url": "https://stripe.com"}'
  → returns JSON report in < 90 seconds

Frontend at localhost:3000
  → enter Stripe URL, see report render
```

If Sai cannot run all four of those, Sprint 1 is not done.
