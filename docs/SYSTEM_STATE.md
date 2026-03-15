# System State — Sprint 0

> Sai reads this at the start of every sprint. 5-minute overview of what exists.

## Current Sprint: 0 (Infrastructure Setup)

### What Works (Sai Can Test)

| Feature | Status | How to Test |
|---------|--------|-------------|
| Git hooks | Active | `git commit -m "bad"` → should reject |
| CI lint workflow | Ready | Push to branch → Actions runs |
| Directory structure | Scaffolded | `ls -la` shows all directories |

### What Doesn't Work Yet

| Feature | Blocking Issue | Owner |
|---------|----------------|-------|
| Pipeline dry-run | No agents implemented | Backend |
| Model client | Not yet created | Backend |
| Vector store | Not yet created | RAG |
| Frontend | Not started | Frontend |
| Evals | No rubrics yet | Evals |

### Sprint 0 Deliverables

- [x] Git hooks configured (conventional commits enforced)
- [x] CI workflow for commit linting
- [x] requirements.txt with pinned dependencies
- [x] .env.example documenting all environment variables
- [x] infra/ module with deploy_target.py and health_check.py
- [x] ADR-001 through ADR-005 documenting infrastructure decisions
- [ ] GCP project created with APIs enabled
- [ ] Service account created with Vertex AI User role
- [ ] Vertex AI API tested with sample call

### Files Changed This Sprint

```
+ requirements.txt
+ .env.example
+ infra/__init__.py
+ infra/deploy_target.py
+ infra/health_check.py
+ docs/decisions/INDEX.md
+ docs/decisions/ADR-001.md (Infrastructure Stack)
+ docs/decisions/ADR-002.md (Authentication)
+ docs/decisions/ADR-003.md (Vector Store)
+ docs/decisions/ADR-004.md (Model Routing)
+ docs/decisions/ADR-005.md (Secrets Management)
+ docs/SYSTEM_STATE.md (this file)
+ docs/ARCHITECTURE.md
```

### Eval Scores

No evals run yet — Sprint 1 will establish baselines.

### Cost This Sprint

$0.00 — no model calls made yet.

### Next Sprint Goals (Sprint 1)

1. `ops/model_client.py` with VertexProvider
2. `agents/base.py` with AgentError contract
3. `agents/scraper.py` basic implementation
4. `agents/consultant.py` with maturity scoring
5. `orchestrator/pipeline.py --dry-run` working
6. Test fixtures for dry-run mode
7. First eval baseline established

### Blockers

| Blocker | Impact | Resolution Path |
|---------|--------|-----------------|
| GCP project not created | Cannot test Vertex AI | Sai creates project |
| Service account not created | Cannot authenticate | Sai creates SA |

### Decision Council Notes

PM, DOC, and Consultant agents provided infrastructure guidance:
- Unanimous on Cloud Run + Vertex AI + ChromaDB stack
- No auth for MVP (defer to Sprint 3)
- ~$0.011 per pipeline run estimated cost
- See ADR-001 through ADR-005 for full rationale
