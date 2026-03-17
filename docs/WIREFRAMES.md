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

---

## 2. Screens

### Screen 1 - Home (/)

```
+----------------------------------------------------------+
| [AI] Discovery Agent                       Tenex Demo    |
+----------------------------------------------------------+
|                                                          |
|           [* AI-Powered Analysis]                        |
|                                                          |
|         AI Transformation Discovery                      |
|                                                          |
|    Enterprise AI maturity assessment in 90 seconds       |
|    from URL to actionable roadmap.                       |
|                                                          |
|  +----------------------------------------------------+  |
|  |  Company URL                                       |  |
|  |  +----------------------------------------------+ |  |
|  |  |  https://stripe.com              [neo-inset]  | |  |
|  |  +----------------------------------------------+ |  |
|  |                                                    |  |
|  |  [        Analyze Company        ] <- accent btn  |  |
|  |                                                    |  |
|  |  [ ] Dry run -- use fixture data, no API cost     |  |
|  +----------------------------------------------------+  |
|                                                          |
|  +----------------------------------------------------+  |
|  |  RECENT ANALYSES                    <- history     |  |
|  |  [stripe.com ....... 3.2 Advancing  2h ago]       |  |
|  |  [acme.com ......... 1.8 Developing 1d ago]       |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
| AI Transformation Discovery Agent         v1.0 Tenex Demo|
+----------------------------------------------------------+
```

- History list only shows when phase is "idle" and localStorage has entries.
- Each row is a neo-flat button: URL (truncated), score+label badge (color-coded), relative time.
- Clicking a row navigates to `/analysis/{run_id}`.
- Dry run defaults to checked.

### Screen 2 - Loading (/ during fetch)

```
+----------------------------------------------------------+
| [AI] Discovery Agent                       Tenex Demo    |
+----------------------------------------------------------+
|  (hero unchanged)                                        |
|                                                          |
|  +----------------------------------------------------+  |
|  |  Company URL                                       |  |
|  |  [  https://stripe.com           ] <- disabled     |  |
|  |  [        Analyzing...           ] <- disabled     |  |
|  |  [ ] Dry run                      <- disabled      |  |
|  +----------------------------------------------------+  |
|                                                          |
|  +----------------------------------------------------+  |
|  |  * Running pipeline -- up to 90 seconds            |  |
|  |                                                    |  |
|  |  [#] 1 Scraping          <- done (blue fill)       |  |
|  |  [o] 2 Querying RAG      <- active, pulsing "..."  |  |
|  |  [ ] 3 Scoring maturity  <- pending (grey)         |  |
|  |  [ ] 4 Writing report    <- pending (grey)         |  |
|  |                                                    |  |
|  |  [Cancel]                                          |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
```

- Steps advance every 18 seconds (cosmetic timer only, not real pipeline status).
- Cancel calls AbortController.abort() and returns to idle.
- History list hidden during loading.

### Screen 3 - Results (/analysis/[runId])

```
+----------------------------------------------------------+
| [AI] Discovery Agent                       Tenex Demo    |
+----------------------------------------------------------+
|                                                          |
|  [Jump to: Exec Summary | Current State | Use Cases |    |
|            ROI Analysis | Roadmap ]    [+ New Analysis]  |
|                                                          |
|  +----------------------------------------------------+  |
|  |  AI Maturity Score                                 |  |
|  |                                                    |  |
|  |  [( 3.2 )]  Advancing          [12.4s]   [$0.01]  |  |
|  |   /5         60th percentile   Runtime    Cost    |  |
|  |                                                    |  |
|  |  DIMENSION BREAKDOWN                               |  |
|  |  Data Infrastructure     [=========--]  3.1       |  |
|  |  ML / AI Capability      [=======----]  2.8       |  |
|  |  Strategy & Intent       [===========]  3.5       |  |
|  |  Operational Readiness   [==========]   3.4       |  |
|  +----------------------------------------------------+  |
|                                                          |
|  id="section-exec-summary"                              |
|  +----------------------------------------------------+  |
|  |  | Executive Summary                              |  |
|  |  [formatted text, paragraphs, bullets, bold]      |  |
|  |  Supporting Evidence  [3 sources]  [v]            |  |
|  +----------------------------------------------------+  |
|                                                          |
|  id="section-current-state"                             |
|  +----------------------------------------------------+  |
|  |  | Current State                                  |  |
|  +----------------------------------------------------+  |
|                                                          |
|  id="section-use-cases"                                 |
|  +----------------------------------------------------+  |
|  |  | AI Use Cases                                   |  |
|  |  [green] Proven Solutions (2 use cases)            |  |
|  |  +--------------------------------------------------+ |
|  |  | [Proven] [Effort: Low] [Impact: High]           | |
|  |  | Title                                           | |
|  |  | CONFIDENCE [==============----------] 70%       | |
|  |  | ROI Estimate: $2M+ annually                     | |
|  |  | Why this company: ...                           | |
|  |  | Data Flow [v]                                   | |
|  |  +--------------------------------------------------+ |
|  |  [amber] Achievable Opportunities (1 use case)     |  |
|  |  [blue]  Frontier Experiments (1 use case)         |  |
|  +----------------------------------------------------+  |
|                                                          |
|  id="section-roi"                                       |
|  +----------------------------------------------------+  |
|  |  | ROI Analysis                                   |  |
|  +----------------------------------------------------+  |
|                                                          |
|  id="section-roadmap"                                   |
|  +----------------------------------------------------+  |
|  |  | Transformation Roadmap                         |  |
|  +----------------------------------------------------+  |
|                                                          |
|  +----------------------------------------------------+  |
|  |  Pipeline Trace -- developer details          [v]  |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
```

- ReportNav tracks scroll. Active button gets blue fill. Clicking smooth-scrolls to section.
- Page fades in on mount (`fadeIn` 300ms, translateY 6px to 0).
- UseCaseTierSection replaces plain ReportCard when `use_cases` array is present and non-empty.
- TracePanel fetches trace data lazily on first expand.

### Screen 4 - Not Found (/analysis/[runId] with missing data)

```
+----------------------------------------------------------+
| [AI] Discovery Agent                       Tenex Demo    |
+----------------------------------------------------------+
|                                                          |
|          +----------------------------------+            |
|          |  Analysis not found             |            |
|          |                                 |            |
|          |  This run ID was not found in   |            |
|          |  your local history. It may     |            |
|          |  have been cleared or opened    |            |
|          |  in a different browser.        |            |
|          |                                 |            |
|          |  [  Run a new analysis  ]       |            |
|          +----------------------------------+            |
|                                                          |
+----------------------------------------------------------+
```

- Brief "Loading analysis..." card shows first while useEffect runs.
- Once ready and data is null, the not-found card replaces it.

---

## 3. User Flow

```
User arrives at /
       |
       v
AnalyzeForm mounts
  - loads localStorage via getHistory()
  - renders URLInputForm
  - renders history list if entries exist
       |
       | user submits URL
       v
phase = "loading"
  - inputs disabled, button shows "Analyzing..."
  - PipelineProgress renders
  - AbortController created
  - POST /v1/analyze { url, dry_run }
       |
       +-- success (status: "complete")
       |   saveAnalysis(url, data) -> localStorage
       |   router.push("/analysis/{run_id}")
       |
       +-- error (non-ok response or status: "failed")
       |   phase = "error"
       |   ErrorMessage renders, "Try again" -> idle
       |
       +-- AbortError (user clicked Cancel)
           phase = "idle"

/analysis/[runId] mounts
  useEffect: getAnalysis(runId) from localStorage
  data found -> ResultsView renders
  data null  -> Not Found card renders
```

### localStorage pattern

All data lives in localStorage under key `analysis_history`.

Structure:
- `entries`: array of up to 10 HistoryEntry objects, newest first.
- `full`: object keyed by run_id, each value is the full AnalyzeSuccess response.

`saveAnalysis(url, data)` writes both on success. Old entries are pruned at 10.
`getHistory()` reads `entries` for the home page list.
`getAnalysis(runId)` reads `full[runId]` for the results page.

---

## 4. Routing

| Route | File | Components |
|-------|------|------------|
| `/` | `frontend/app/page.tsx` | RootLayout -> HomePage -> AnalyzeForm -> URLInputForm, PipelineProgress, ErrorMessage, history list |
| `/analysis/[runId]` | `frontend/app/analysis/[runId]/page.tsx` | RootLayout -> AnalysisResultPage -> ResultsView or not-found card |

Both routes share the header and footer from `frontend/app/layout.tsx`.
The app uses Next.js App Router.

---

## 5. Design System

### Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--neo-bg` | `#edf0f5` | Card backgrounds |
| `--neo-shadow-dark` | `#c4cad6` | Shadow dark side |
| `--neo-shadow-light` | `#ffffff` | Shadow light side |
| `--accent` | `#4f6df5` | Buttons, active states, progress bars |
| Heading | `#1e2433` | Primary text |
| Body | `#4a5568` | Paragraph text |
| Muted | `#718096` | Labels, metadata |
| Error | `#e53e3e` | Error states |
| Success tier | `#16a34a` | Proven Solutions (green) |
| Warning tier | `#d97706` | Achievable Opportunities (amber) |

### Neomorphic Utilities

| Class | Effect |
|-------|--------|
| `.neo-raised` | `6px 6px 14px #c4cad6, -6px -6px 14px #fff` - primary cards |
| `.neo-flat` | `3px 3px 8px #c4cad6, -3px -3px 8px #fff` - secondary cards, nav, history rows |
| `.neo-inset` | `inset 3px 3px 7px #c4cad6, inset -3px -3px 7px #fff` - input fields |
| `.neo-btn` | `4px 4px 10px #c4cad6, -4px -4px 10px #fff` - plain buttons |
| `.btn-accent` | Blue gradient + directional shadow - primary CTA |

Border radius: 16px on all cards. 12px on inputs.

### Typography

- Font: Inter (Google Fonts).
- h1: 32px, extrabold, tracking-tight, `#1e2433`.
- Section titles: 16px, bold, `#1e2433`.
- Body: 14px, line-height 1.75, `#4a5568`.
- Labels/badges: 10-12px, semibold, uppercase with letter-spacing.

### Animations

- `.page-fade-in`: opacity 0 + translateY 6px to visible, 300ms ease-out. Applied to ResultsView.
- Pipeline dots: `animate-pulse` on active step.
- Dimension bars: `transition-all duration-500` for width on mount.
- Confidence bars in UseCaseCard: same `transition-all duration-500`.

### Maturity Score Colors

| Score | Color | Tier |
|-------|-------|------|
| < 2.0 | red `#ef4444` | Initial / Developing |
| 2.0 - 3.4 | amber `#f59e0b` | Advancing |
| 3.5+ | blue `#4f6df5` | Leading / Transformational |

### History Row Badge Colors

| Score | Background | Text |
|-------|-----------|------|
| >= 4.0 | `#e8f0fe` | `#3b5de7` (blue) |
| 2.5 - 3.9 | `#fef9e7` | `#b7791f` (amber) |
| < 2.5 | `#fdecea` | `#c0392b` (red) |
