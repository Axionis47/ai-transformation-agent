# Frontend

The frontend is a Next.js 14 application with React 18, TypeScript, and Tailwind CSS.
It renders what the backend tells it to render. All business logic lives on the backend.

---

## Tech Stack

| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 14.2 | App Router, SSR/CSR |
| React | 18.3 | UI rendering |
| TypeScript | 5.5 | Type safety |
| Tailwind CSS | 3.4 | Styling |

No UI library (no Material, no shadcn). All components are custom.

---

## How it talks to the backend

All API calls go through `frontend/lib/api.ts`. The base URL comes from
`NEXT_PUBLIC_API_URL` (defaults to empty string, meaning same-origin).

In development: `NEXT_PUBLIC_API_URL=http://localhost:8000` (set by dev.sh).

The API client is a thin wrapper around `fetch()`:
- All requests include `Content-Type: application/json`
- All responses are parsed as JSON
- Errors throw with the HTTP status and response text

There is no WebSocket or SSE. The frontend polls the backend for updates.

---

## Pages

### Home Page: `/` (app/page.tsx)

The landing page. Users start here.

**What it shows**:
- Intake form (company name, industry, employee count band, notes)
- Depth slider (1-10) and confidence threshold slider (0.3-1.0)
- System status indicator (backend online/offline via GET /health)
- System defaults (from GET /v1/defaults): search budget, RAG budget, models, pipeline stages
- Recent runs list (stored in localStorage, max 8 entries)

**User flow**:
1. Fill in the intake form
2. Adjust depth/confidence sliders
3. Click "Begin Analysis"
4. Frontend calls: POST /v1/runs -> PUT /v1/runs/{id}/company-intake -> POST /v1/runs/{id}/start
5. Saves to recent runs in localStorage
6. Navigates to `/run/{id}`

---

### Run Dashboard: `/run/[id]` (app/run/[id]/page.tsx)

The main workspace during pipeline execution. Shows live progress.

**What it shows**:
- Phase progress rail (8 phases: INTAKE through PUBLISHED)
- Phase-specific content via RunPhaseContent component
- Agent activity panel (during agent phases)
- Hypothesis list (during hypothesis phases)
- Interaction modal (when an agent surfaces a question)

**Polling behavior**:
- During active phases (grounding, deep_research, hypothesis_formation, hypothesis_testing, synthesis): polls GET /runs/{id} every few seconds
- During agent phases: also polls GET /runs/{id}/agents and GET /runs/{id}/hypotheses
- Checks for pending interactions via GET /runs/{id}/interactions
- Stops polling when run reaches a terminal state (review, published, failed)

**Phase-specific content**:
- **INTAKE**: editable intake form
- **GROUNDING/DEEP_RESEARCH**: agent activity panel showing which agents are running
- **HYPOTHESIS_FORMATION/TESTING**: hypothesis list with status/confidence per hypothesis
- **REVIEW**: links to report page, approve/investigate buttons
- **PUBLISHED**: link to report

---

### Report Page: `/run/[id]/report` (app/run/[id]/report/page.tsx)

Displays the AdaptiveReport.

**What it shows**:
- Executive summary
- Key insight
- Opportunities (sorted by confidence, color-coded by tier):
  - Easy (Quick Win) -- mint/green border, 4-6 weeks timeline
  - Medium (Strategic Initiative) -- amber border, 2-3 months
  - Hard (Transformation) -- rose/red border, 6+ months
- Each opportunity: title, narrative, tier badge, confidence, evidence summary, risks, conditions, recommended approach
- Reasoning chain (how the analysis reached its conclusions)
- Confidence assessment narrative
- What we don't know (gaps and uncertainties)
- Recommended next steps
- Evidence annex (filterable, with scroll-to anchors)

**User actions**:
- **Approve**: POST /review/approve -> transitions to PUBLISHED
- **Investigate**: POST /review/investigate -> returns to HYPOTHESIS_TESTING
- **Feedback**: inline feedback buttons per section. User enters instruction, selects type (edit/deepen/reinvestigate), submits via POST /report/refine
- **Enrich**: link to enrichment page

---

### Trace Page: `/run/[id]/trace` (app/run/[id]/trace/page.tsx)

Developer/debug view. Shows the raw trace event log.

**What it shows**:
- Chronological list of all trace events for the run
- Color-coded by phase (grounding=indigo, research=amber, testing=mint)
- Human-readable labels for event types (e.g., AGENT_SPAWNED -> "Agent Spawned")
- Expandable payload for each event
- Agent states summary

---

### Enrichment Page: `/run/[id]/enrich` (app/run/[id]/enrich/page.tsx)

Form for injecting analyst-provided evidence.

**What it shows**:
- List of current hypotheses (for targeting)
- Enrichment form: category, title, detail, confidence, affected hypotheses
- After submission: shows confidence deltas (before/after per hypothesis)

**User flow**:
1. Select enrichment category (technology, operations, pain_points, etc.)
2. Enter title and detail
3. Optionally select affected hypotheses
4. Submit -> POST /runs/{id}/enrich
5. See result: evidence added, hypotheses affected, confidence changes

---

### Login Page: `/login` (app/login/page.tsx)

Stub. Not implemented. No authentication in the system currently.

---

## Components

### Layout & Shell

| Component | File | Purpose |
|-----------|------|---------|
| Header | `components/shell/Header.tsx` | Top navigation bar |
| Sidebar | `components/shell/Sidebar.tsx` | Side navigation |

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| IntakeForm | `components/IntakeForm.tsx` | Company intake form with depth/confidence sliders |
| RunPhaseContent | `components/RunPhaseContent.tsx` | Switches content based on current pipeline phase |
| PhaseProgress | `components/PhaseProgress.tsx` | Phase progress rail (8 stages) |
| ProgressRail | `components/ProgressRail.tsx` | Visual progress indicator |
| AgentActivityPanel | `components/AgentActivityPanel.tsx` | Shows which agents are running and their status |
| HypothesisList | `components/HypothesisList.tsx` | Filterable list of hypotheses with status/confidence |
| InteractionModal | `components/InteractionModal.tsx` | Modal for answering agent questions |

### Report Components

| Component | File | Purpose |
|-----------|------|---------|
| AdaptiveReportView | `components/AdaptiveReportView.tsx` | Full adaptive report rendering |
| ReportView | `components/ReportView.tsx` | Legacy report rendering |
| ReasoningChain | `components/ReasoningChain.tsx` | Displays hypothesis reasoning steps |
| ConfidenceNarrative | `components/ConfidenceNarrative.tsx` | Confidence assessment text |
| EvidenceAnnex | `components/EvidenceAnnex.tsx` | Filterable evidence list with scroll anchors |
| EvidenceBlock | `components/EvidenceBlock.tsx` | Single evidence block |
| FeedbackButton | `components/FeedbackButton.tsx` | Inline feedback control per report section |
| OpportunityRow | `components/OpportunityRow.tsx` | Single opportunity in report |
| EnrichForm | `components/EnrichForm.tsx` | Enrichment input form |

### Cards

| Component | File | Purpose |
|-----------|------|---------|
| HypothesisCard | `components/cards/HypothesisCard.tsx` | Single hypothesis with status/confidence |
| EvidenceCard | `components/cards/EvidenceCard.tsx` | Single evidence item |
| AssumptionCard | `components/cards/AssumptionCard.tsx` | Single assumption (legacy) |
| OpportunityCard | `components/cards/OpportunityCard.tsx` | Single opportunity card |

### Stage-Specific

| Component | File | Purpose |
|-----------|------|---------|
| ReasoningStage | `components/stages/ReasoningStage.tsx` | Legacy reasoning loop view |
| ReasoningView | `components/ReasoningView.tsx` | Reasoning state display |
| AssumptionsReview | `components/AssumptionsReview.tsx` | Assumptions editor (legacy) |
| StageSection | `components/StageSection.tsx` | Generic stage content wrapper |

### UI Primitives

| Component | File | Purpose |
|-----------|------|---------|
| Badge | `components/ui/Badge.tsx` | Colored status badge |
| TierBadge | `components/ui/TierBadge.tsx` | Opportunity tier indicator |
| ScoreBar | `components/ui/ScoreBar.tsx` | Visual score bar |
| Spinner | `components/ui/Spinner.tsx` | Loading indicator |
| BudgetPills | `components/BudgetPills.tsx` | Budget remaining counters |
| DataRow | `components/DataRow.tsx` | Key-value display row |

---

## User Flow (End to End)

```
1. User opens http://localhost:3000
   -> Home page loads
   -> GET /health (check backend)
   -> GET /v1/defaults (load config)

2. User fills intake form, clicks "Begin Analysis"
   -> POST /v1/runs (create run)
   -> PUT /v1/runs/{id}/company-intake (save intake)
   -> POST /v1/runs/{id}/start (fire and forget)
   -> Navigate to /run/{id}

3. Run dashboard shows progress
   -> Polls GET /v1/runs/{id} every few seconds
   -> Polls GET /v1/runs/{id}/agents (during agent phases)
   -> Polls GET /v1/runs/{id}/hypotheses (during hypothesis phases)
   -> Polls GET /v1/runs/{id}/interactions (checks for questions)

4. If agent surfaces a question:
   -> InteractionModal opens
   -> User types answer
   -> POST /v1/runs/{id}/interactions/{iid}/respond

5. Pipeline reaches REVIEW:
   -> Dashboard shows "Report Ready"
   -> User clicks to view report
   -> Navigate to /run/{id}/report

6. Report page shows full analysis:
   -> GET /v1/runs/{id}/report (load report)
   -> GET /v1/runs/{id}/evidence (load evidence for annex)
   -> User can approve, investigate, or refine

7a. User approves:
    -> POST /v1/runs/{id}/review/approve
    -> Run transitions to PUBLISHED

7b. User provides feedback:
    -> POST /v1/runs/{id}/report/refine
    -> Report regenerated, user sees updated version

7c. User enriches:
    -> Navigate to /run/{id}/enrich
    -> Fill enrichment form
    -> POST /v1/runs/{id}/enrich
    -> See confidence deltas
```

---

## Styling

The app uses Tailwind CSS with custom color tokens defined in `tailwind.config.ts`:

| Token | Usage |
|-------|-------|
| canvas | Page background |
| canvas-raised | Card/panel background |
| ink | Primary text |
| ink-secondary | Secondary text |
| ink-tertiary | Muted text |
| edge-subtle | Borders |
| mint | Success, "easy" tier, online status |
| amber | Warning, "medium" tier |
| rose | Error, "hard" tier, offline status |

The UI is responsive (sidebar + main content layout). Font is monospace.

---

## What the frontend does NOT do

- No authentication (login page is a stub)
- No WebSocket/SSE (polls for updates)
- No PDF export (report renders as HTML only)
- No offline support
- No client-side state management library (uses React useState + useEffect)
- No business logic (all decisions happen on the backend)
