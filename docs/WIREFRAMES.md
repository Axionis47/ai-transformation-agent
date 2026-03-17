# WIREFRAMES.md

Last updated: Sprint 6. Written from actual code, not from design specs.

---

## 1. Component Inventory

Every component is built and in production. None are pending.

### Layout

| Component | File | What it renders |
|-----------|------|-----------------|
| RootLayout | `frontend/app/layout.tsx` | Persistent shell: header, main, footer. Wraps every page. |

RootLayout details.
- Header: fixed top bar, blurred glass (`rgba(237,240,245,0.85)` + backdrop blur 8px). "AI" logo badge links to `/`. Right side shows "Tenex Demo".
- Main: `max-w-2xl mx-auto px-6 py-10`. Renders `{children}`.
- Footer: full-width border-top. Left: product name. Right: "v1.0 - Tenex Demo".
- Font: Inter via next/font/google.
- Body background: `linear-gradient(135deg, #edf0f5, #e8ecf2, #eaecf5)` fixed.

### Home Page Components

| Component | File | Props | What it renders |
|-----------|------|-------|-----------------|
| AnalyzeForm | `frontend/components/AnalyzeForm.tsx` | none | PageState machine: idle, loading, error. Renders URLInputForm, PipelineProgress, ErrorMessage, history list. |
| URLInputForm | `frontend/components/URLInputForm.tsx` | `onSubmit`, `isLoading` | Neo-raised card with URL input, accent button, dry-run checkbox. |
| PipelineProgress | `frontend/components/PipelineProgress.tsx` | `onCancel?` | 4 animated steps (Scraping, Querying RAG, Scoring maturity, Writing report). Advances every 18s. Cancel button. |
| ErrorMessage | `frontend/components/ErrorMessage.tsx` | `message`, `onReset` | Neo-raised card, red left border, red icon, error text, "Try again" button. |

### Results Page Components

| Component | File | Props | What it renders |
|-----------|------|-------|-----------------|
| ResultsView | `frontend/components/ResultsView.tsx` | `data: AnalyzeSuccess` | Full results layout: ReportNav, MaturityBadge, 5 report sections, TracePanel. `page-fade-in` animation. |
| ReportNav | `frontend/components/ReportNav.tsx` | none | Horizontal pill nav with 5 section links. Active section gets blue fill. Tracks scroll position. |
| MaturityBadge | `frontend/components/MaturityBadge.tsx` | `score?`, `label?`, `elapsedSeconds?`, `costUsd?`, `dimensions?` | Neo-raised card. Score ring (conic gradient, 80x80px), tier label, percentile pill, Runtime and Cost stat chips, 4-dimension bar grid. |
| ReportCard | `frontend/components/ReportCard.tsx` | `title`, `content`, `wins?`, `id?` | Neo-raised card. Blue accent bar, title, formatted content (markdown-like), optional EvidencePanel. |
| EvidencePanel | `frontend/components/EvidencePanel.tsx` | `wins: VictoryMatch[]` | Collapsible inside ReportCard. Shows VictoryMatch cards with win_id, title, tier badge (Direct/Calibration/Adjacent), similarity %, confidence %, relevance note, ROI benchmark, gap analysis. |
| UseCaseTierSection | `frontend/components/UseCaseTierSection.tsx` | `useCases: TieredUseCase[]`, `id?` | Neo-raised card. Groups use cases into 3 tiers: Proven Solutions (green), Achievable Opportunities (amber), Frontier Experiments (blue). Each tier has a header pill and UseCaseCards. |
| UseCaseCard | `frontend/components/UseCaseCard.tsx` | `useCase: TieredUseCase` | Neo-flat card with colored left border. Tier/effort/impact tags, title, description, confidence bar, ROI estimate, "Why this company", RAG benchmark, collapsible Data Flow accordion. |
| TracePanel | `frontend/components/TracePanel.tsx` | `runId: string \| null` | Collapsible developer panel. Fetches `GET /v1/trace/{runId}` lazily on first open. Shows skeleton, error, or TraceStageRows. |
| TraceStageRow | `frontend/components/TraceStageRow.tsx` | `stage: TraceStage` | Row in TracePanel. Agent tag badge, latency chip, prompt file. Expands to input/output summary tables. |
