# API Reference

Every HTTP endpoint in the system, grouped by user flow.
All routes are registered in `api/app.py` under the `/v1/` prefix.
Route files live in `api/routes/`.

---

## Health & Config

### GET /health

Returns system health status.

**Response**: `{"status": "ok"}`

**File**: `api/app.py:54`

---

### GET /v1/defaults

Returns default configuration values for the frontend home page.
No hardcoded values in the frontend -- everything comes from here.

**Response**:
```json
{
  "rag_budget": 15,
  "search_budget": 25,
  "search_max_calls": 8,
  "reasoning_model": "gemini-2.5-flash",
  "synthesis_model": "gemini-2.5-pro",
  "pipeline_stages": ["Intake", "Grounding", "Deep Research", ...]
}
```

**File**: `api/app.py:59`

---

## Run Lifecycle

### POST /v1/runs

Create a new run. Returns a Run object with a UUID.

**Request body**:
```json
{
  "company_name": "Acme Corp",
  "industry": "logistics",
  "reasoning_depth": 5,
  "confidence_threshold": 0.7
}
```

`reasoning_depth` (1-10, optional) and `confidence_threshold` (0.1-1.0, optional) are
the user's slider values. They're injected as config overrides and frozen into the run's
config_snapshot.

**Response**: Full `Run` object (status: "created")

**File**: `api/routes/runs.py:22`

---

### GET /v1/runs/{run_id}

Fetch full run state including evidence, hypotheses, report, agent states, etc.

**Response**: Full `Run` object

**File**: `api/routes/runs.py:38`

---

### PUT /v1/runs/{run_id}/company-intake

Save company intake details. Transitions run to INTAKE status.

**Request body**:
```json
{
  "company_name": "Acme Corp",
  "industry": "logistics",
  "employee_count_band": "100-500",
  "notes": "Fleet management company",
  "constraints": ["no cloud migration"]
}
```

**Response**: Updated `Run` object (status: "intake")

**File**: `api/routes/runs.py:46`

---

### POST /v1/runs/{run_id}/start

Triggers the pipeline. Behavior depends on orchestration mode.

**Multi-agent mode** (default):
- Spawns the Orchestrator in a background daemon thread
- Returns the Run immediately (status still "intake")
- Orchestrator handles all state transitions in the background
- Frontend polls GET /runs/{id} and GET /runs/{id}/trace for progress

**Legacy mode**:
- If status is INTAKE: generates assumptions, transitions to ASSUMPTIONS_DRAFT
- If status is ASSUMPTIONS_CONFIRMED: runs reasoning loop

**Response**: `Run` object (multi-agent) or `AssumptionsDraft` / `ReasoningLoopResult` (legacy)

**File**: `api/routes/thought.py:59`

---

### GET /v1/runs/{run_id}/trace

Returns all trace events for a run, ordered chronologically.

**Response**: `TraceEvent[]`

**File**: `api/routes/runs.py:53`

---

## Pipeline Interaction (Legacy Mode)

### POST /v1/runs/{run_id}/assumptions/confirm

Confirm (or edit) assumptions. Transitions from ASSUMPTIONS_DRAFT to ASSUMPTIONS_CONFIRMED.

**Request body** (optional): `AssumptionsDraft` with edited assumptions. If omitted, confirms as-is.

**Response**: Updated `Run` object

**File**: `api/routes/thought.py:151`

---

### POST /v1/runs/{run_id}/answer

User answers an escalation question from the reasoning loop. Converts the answer to
USER_PROVIDED evidence (relevance=1.0, confidence=1.0) and resumes the reasoning loop.

**Request body**:
```json
{
  "question_id": "q-abc123",
  "answer_text": "We use SAP for ERP and Salesforce for CRM"
}
```

**Requires**: Run in REASONING status with a pending question

**Response**: `ReasoningLoopResult`

**File**: `api/routes/thought.py:175`

---

## Multi-Agent Endpoints

### GET /v1/runs/{run_id}/agents

List all agent execution records for a run.

**Response**:
```json
{
  "agents": [AgentState, ...],
  "count": 6
}
```

**File**: `api/routes/agents.py:68`

---

### GET /v1/runs/{run_id}/hypotheses

List all hypotheses with their current status and confidence.

**Response**:
```json
{
  "hypotheses": [Hypothesis, ...],
  "count": 5
}
```

**File**: `api/routes/agents.py:74`

---

### GET /v1/runs/{run_id}/hypotheses/{hid}

Get a single hypothesis with full detail (reasoning chain, test results, evidence links).

**Response**: `Hypothesis`

**File**: `api/routes/agents.py:80`

---

### GET /v1/runs/{run_id}/interactions

List user interaction points (questions or findings surfaced by agents).

**Response**:
```json
{
  "interactions": [UserInteractionPoint, ...],
  "pending": 1,
  "resolved": 3
}
```

**File**: `api/routes/agents.py:89`

---

### POST /v1/runs/{run_id}/interactions/{iid}/respond

Respond to a user interaction point.

**Request body**:
```json
{
  "interaction_id": "int-abc123",
  "response": "Yes, we have a dedicated IT team of 12"
}
```

**Response**: Updated `UserInteractionPoint`

**File**: `api/routes/agents.py:102`

---

## Review & Report

### GET /v1/runs/{run_id}/report

Get the report. Returns AdaptiveReport (multi-agent) or legacy report dict.

**Response**: Report object (executive_summary, opportunities, evidence_annex, etc.)

**File**: `api/routes/pitch.py:191`

---

### POST /v1/runs/{run_id}/review/approve

Approve the report and publish. Transitions REVIEW -> PUBLISHED.

**Requires**: Run in REVIEW status

**Response**:
```json
{
  "run_id": "...",
  "status": "published",
  "message": "Report approved and published"
}
```

**File**: `api/routes/agents.py:114`

---

### POST /v1/runs/{run_id}/review/investigate

Return to hypothesis testing for deeper investigation. Transitions REVIEW -> HYPOTHESIS_TESTING.

**Requires**: Run in REVIEW status

**Response**:
```json
{
  "run_id": "...",
  "status": "hypothesis_testing",
  "message": "Returning to hypothesis testing for deeper investigation"
}
```

**File**: `api/routes/agents.py:126`

---

### POST /v1/runs/{run_id}/report/refine

Refine the report based on user feedback. Handles three feedback types:

- **edit**: Re-synthesizes the report with feedback instructions. Stays at REVIEW.
- **deepen**: Re-tests targeted hypotheses, then re-synthesizes. Stays at REVIEW.
- **reinvestigate**: Transitions to DEEP_RESEARCH for full re-run.

**Request body**:
```json
{
  "feedbacks": [
    {
      "feedback_type": "edit",
      "target_section": "executive_summary",
      "instruction": "Make the summary more concise"
    },
    {
      "feedback_type": "deepen",
      "target_section": "opportunity:hyp-abc123",
      "instruction": "Find more evidence for this claim"
    }
  ]
}
```

**Requires**: Run in REVIEW status

**Response**: Updated `Run` object

**File**: `api/routes/agents.py:142`

---

### POST /v1/runs/{run_id}/enrich

Inject analyst-provided evidence, re-test affected hypotheses, regenerate report.

**Request body**:
```json
{
  "inputs": [
    {
      "category": "technology",
      "title": "They use SAP S/4HANA",
      "detail": "Company migrated to SAP S/4HANA in 2023, full ERP integration",
      "affected_hypothesis_ids": ["hyp-abc123"],
      "confidence": 0.9
    }
  ]
}
```

Categories: technology, financials, operations, pain_points, constraints, corrections, additional_context

**Requires**: Run in REVIEW or PUBLISHED status

**Response**:
```json
{
  "run_id": "...",
  "evidence_added": 1,
  "hypotheses_affected": 2,
  "deltas": [
    {
      "hypothesis_id": "hyp-abc123",
      "statement": "AI dispatch optimization...",
      "confidence_before": 0.65,
      "confidence_after": 0.78,
      "status_before": "validated",
      "status_after": "validated"
    }
  ],
  "message": "Enrichment complete: 2 hypotheses re-evaluated"
}
```

**File**: `api/routes/agents.py:252`

---

## Legacy Synthesis

### POST /v1/runs/{run_id}/synthesize

Run pitch synthesis (legacy mode). Generates opportunities and report from reasoning loop results.

**Requires**: Run in REASONING status with completed=true

**Response**: `{"opportunities": [...], "tier_counts": {"easy": 1, "medium": 2}}`

**File**: `api/routes/pitch.py:40`

---

### POST /v1/runs/{run_id}/publish

Publish report (legacy mode). Transitions REPORT -> PUBLISHED.

**Response**: Updated `Run` object

**File**: `api/routes/pitch.py:107`

---

### POST /v1/runs/{run_id}/refine

Apply corrections and re-score (legacy mode). Corrects assumptions, removes opportunities,
adds user context as evidence, and re-composes the report.

**Request body**:
```json
{
  "corrections": [{"field": "company_size", "new_value": "500", "reason": "Actual headcount"}],
  "removed_opportunity_ids": ["opp-xyz"],
  "additional_context": "We already have an ML team of 5"
}
```

**Response**: `{"report": {...}, "changes": {...}}`

**File**: `api/routes/pitch.py:119`

---

### GET /v1/runs/{run_id}/evidence

Get all promoted evidence for a run, sorted by relevance.

**Response**: `EvidenceItem[]`

**File**: `api/routes/pitch.py:183`

---

### GET /v1/runs/{run_id}/opportunities

Get scored opportunities (legacy mode).

**Response**: `Opportunity[]`

**File**: `api/routes/pitch.py:203`

---

## Direct Service Access

### POST /v1/runs/{run_id}/ground

Run a Gemini grounding call directly. Useful for debugging.

**Request body**: `{"prompt": "What does Acme Corp do?"}`

**Response**: `GroundingResult` (text, evidence_items, search_queries_used, budget_exhausted)

**File**: `api/routes/grounding.py:34`

---

### POST /v1/runs/{run_id}/rag:query

Query the RAG knowledge base directly. Useful for debugging.

**Request body**: `{"query": "fleet management automation"}`

**Response**: `RAGQueryResult` (results, query, budget_exhausted, filtered_count)

**File**: `api/routes/rag.py:18`

---

## Backend-Driven UI

### GET /v1/runs/{run_id}/ui

Returns UI hints for the current run status. The frontend renders whatever this endpoint says.

**Response**: `UIHints` with stage_title, stage_description, actions (buttons), editable_fields (forms), budget_view (remaining queries), and optional agent_message.

Each status returns different hints:
- **CREATED**: intake form + submit button
- **INTAKE**: "Start Analysis" button
- **ASSUMPTIONS_DRAFT**: assumption editor + confirm/edit buttons
- **REASONING**: answer question button
- **SYNTHESIS**: waiting state
- **REPORT**: publish button
- **PUBLISHED/FAILED**: view report link

**File**: `api/routes/ui.py:203`

---

## Endpoint Summary Table

| Method | Path | Purpose | Mode |
|--------|------|---------|------|
| GET | /health | Health check | Both |
| GET | /v1/defaults | System config for frontend | Both |
| POST | /v1/runs | Create run | Both |
| GET | /v1/runs/{id} | Get run state | Both |
| PUT | /v1/runs/{id}/company-intake | Save intake | Both |
| POST | /v1/runs/{id}/start | Trigger pipeline | Both |
| GET | /v1/runs/{id}/trace | Get trace events | Both |
| GET | /v1/runs/{id}/ui | Backend-driven UI hints | Both |
| GET | /v1/runs/{id}/agents | List agent states | Multi-agent |
| GET | /v1/runs/{id}/hypotheses | List hypotheses | Multi-agent |
| GET | /v1/runs/{id}/hypotheses/{hid} | Get hypothesis detail | Multi-agent |
| GET | /v1/runs/{id}/interactions | List user interactions | Multi-agent |
| POST | /v1/runs/{id}/interactions/{iid}/respond | Respond to interaction | Multi-agent |
| POST | /v1/runs/{id}/review/approve | Approve report | Multi-agent |
| POST | /v1/runs/{id}/review/investigate | Return to testing | Multi-agent |
| POST | /v1/runs/{id}/report/refine | Refine report | Multi-agent |
| POST | /v1/runs/{id}/enrich | Add evidence + re-test | Multi-agent |
| GET | /v1/runs/{id}/report | Get report | Both |
| GET | /v1/runs/{id}/evidence | Get evidence | Both |
| GET | /v1/runs/{id}/opportunities | Get opportunities | Legacy |
| POST | /v1/runs/{id}/assumptions/confirm | Confirm assumptions | Legacy |
| POST | /v1/runs/{id}/answer | Answer question | Legacy |
| POST | /v1/runs/{id}/synthesize | Run pitch synthesis | Legacy |
| POST | /v1/runs/{id}/publish | Publish report | Legacy |
| POST | /v1/runs/{id}/refine | Correct + re-score | Legacy |
| POST | /v1/runs/{id}/ground | Direct grounding call | Debug |
| POST | /v1/runs/{id}/rag:query | Direct RAG query | Debug |
