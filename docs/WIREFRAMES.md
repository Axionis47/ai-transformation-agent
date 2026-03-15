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
