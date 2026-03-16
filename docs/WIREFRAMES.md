# UI Component Inventory

## Status Legend
- Pending: Not started
- In Progress: Being built
- Ready: Works in Storybook
- Deployed: Live in production

## Components

### Input Components

| Component | Status | Owner | Storybook |
|-----------|--------|-------|-----------|
| URLInput | Pending | Frontend | - |
| AnalyzeButton | Pending | Frontend | - |

### Status Components

| Component | Status | Owner | Storybook |
|-----------|--------|-------|-----------|
| PipelineStatus | Pending | Frontend | - |
| AgentStatusCard | Pending | Frontend | - |
| ProgressIndicator | Pending | Frontend | - |
| ErrorMessage | Pending | Frontend | - |

### Report Components

| Component | Status | Owner | Storybook |
|-----------|--------|-------|-----------|
| ReportContainer | Pending | Frontend | - |
| ExecSummaryCard | Pending | Frontend | - |
| MaturityScoreCard | Pending | Frontend | - |
| UseCaseCard | Pending | Frontend | - |
| ROIChart | Pending | Frontend | - |
| RoadmapTimeline | Pending | Frontend | - |

### Layout Components

| Component | Status | Owner | Storybook |
|-----------|--------|-------|-----------|
| AppShell | Pending | Frontend | - |
| Header | Pending | Frontend | - |
| Footer | Pending | Frontend | - |

## Design System

### Neomorphic Tokens

```css
/* Base colors */
--neo-bg: #e0e5ec;
--neo-shadow-dark: #a3b1c6;
--neo-shadow-light: #ffffff;

/* Elevation */
--neo-raised:
  6px 6px 12px var(--neo-shadow-dark),
  -6px -6px 12px var(--neo-shadow-light);

--neo-inset:
  inset 6px 6px 12px var(--neo-shadow-dark),
  inset -6px -6px 12px var(--neo-shadow-light);

/* Border radius */
--neo-radius-sm: 8px;
--neo-radius-md: 16px;
--neo-radius-lg: 24px;
```

### Typography

```css
/* Font stack */
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Sizes */
--text-xs: 0.75rem;
--text-sm: 0.875rem;
--text-base: 1rem;
--text-lg: 1.125rem;
--text-xl: 1.25rem;
--text-2xl: 1.5rem;
```

## Wireframes

### Main Page (URL Input)

```
┌────────────────────────────────────────────────────────────┐
│  AI Transformation Discovery                         [?]   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│                                                            │
│     ┌────────────────────────────────────────────────┐    │
│     │  Enter company URL...                          │    │
│     └────────────────────────────────────────────────┘    │
│                                                            │
│                   ┌──────────────┐                         │
│                   │   Analyze    │                         │
│                   └──────────────┘                         │
│                                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Analysis In Progress

```
┌────────────────────────────────────────────────────────────┐
│  Analyzing: example.com                                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  [✓] Scraping company pages              2.3s        │ │
│  │  [▶] Analyzing AI maturity               ...         │ │
│  │  [ ] Finding similar companies                       │ │
│  │  [ ] Generating report                               │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│                  Estimated: 45 seconds                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Report View

```
┌────────────────────────────────────────────────────────────┐
│  AI Transformation Report: Example Corp           [Export] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────┐  ┌─────────────────────────────┐ │
│  │  Maturity Score     │  │  Executive Summary          │ │
│  │                     │  │                             │ │
│  │      ████░░  3.2    │  │  Example Corp is in the     │ │
│  │     Emerging        │  │  Emerging stage of AI...    │ │
│  │                     │  │                             │ │
│  └─────────────────────┘  └─────────────────────────────┘ │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Top Use Cases                                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐      │   │
│  │  │ Use Case 1 │ │ Use Case 2 │ │ Use Case 3 │      │   │
│  │  │ High Impact│ │ Med Impact │ │ High Impact│      │   │
│  │  │ Low Effort │ │ Low Effort │ │ Med Effort │      │   │
│  │  └────────────┘ └────────────┘ └────────────┘      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Implementation Roadmap                             │   │
│  │  ──●────────●────────●────────●──▶                 │   │
│  │   Q1       Q2       Q3       Q4                     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Trace Panel (below Report View — Sprint 5)

```
┌────────────────────────────────────────────────────────────┐
│  AI Transformation Report: Example Corp           [Export] │
├────────────────────────────────────────────────────────────┤
│  ... report sections above ...                             │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  ▼  Pipeline Trace  (run_id: abc-123)                │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │ Stage 1: website_scraper          ✓  0.8s      │  │ │
│  │  │ IN:  { url: "example.com" }                    │  │ │
│  │  │ OUT: { pages: 3, chars: 8400 }                 │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │ Stage 2: signal_extractor         ✓  2.1s      │  │ │
│  │  │ IN:  { pages_count: 3 }                        │  │ │
│  │  │ OUT: { signal_count: 9 }                       │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │ Stage 3: maturity_scorer          ✓  3.4s      │  │ │
│  │  │ IN:  { signal_count: 9 }                       │  │ │
│  │  │ OUT: { maturity_score: 3.2, label: Emerging }  │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │ Stage 4: victory_matcher          ✓  2.8s      │  │ │
│  │  │ Stage 5: use_case_generator       ✓  8.2s      │  │ │
│  │  │ Stage 6: report_writer            ✓  6.1s      │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

Component: `frontend/components/TracePanel.tsx`
Data source: `GET /v1/trace/{run_id}`
State: collapsed by default, expands on click
Error state: shows "Trace unavailable" if run_id not found

### Component Inventory — Sprint 5 Updates

| Component | Status | Storybook |
|-----------|--------|-----------|
| URLInput | Ready | - |
| ReportRenderer | Ready | - |
| UseCaseCard | Ready | Yes |
| UseCaseTierSection | Ready | Yes |
| TracePanel | Ready | Yes |
| TraceStageRow | Ready | (via TracePanel story) |
