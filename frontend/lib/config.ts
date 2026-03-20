// ── API ──
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Score Colors ──
export const SCORE_COLORS = {
  low: "#c1272d",
  mid: "#1a1714",
  high: "#2d6a4f",
} as const;

export function scoreColor(score: number): string {
  if (score > 3.5) return SCORE_COLORS.high;
  if (score >= 2) return SCORE_COLORS.mid;
  return SCORE_COLORS.low;
}

// ── Maturity Tiers ──
export const MATURITY_TIERS = [
  { max: 1.5, label: "Initial" },
  { max: 2.5, label: "Developing" },
  { max: 3.5, label: "Advancing" },
  { max: 4.5, label: "Leading" },
  { max: Infinity, label: "Transformational" },
] as const;

export function maturityTier(score: number): string {
  for (const tier of MATURITY_TIERS) {
    if (score < tier.max) return tier.label;
  }
  return "Transformational";
}

// ── Use Case Tier Config ──
export const USE_CASE_TIERS = {
  LOW_HANGING_FRUIT: {
    heading: "PROVEN SOLUTIONS",
    subtitle: "Validated approaches with direct evidence",
    accent: "#2d6a4f",
  },
  MEDIUM_SOLUTION: {
    heading: "ADAPTED APPROACHES",
    subtitle: "Modified from adjacent wins",
    accent: "#6b5b4f",
  },
  HARD_EXPERIMENT: {
    heading: "EXPERIMENTAL OPPORTUNITIES",
    subtitle: "Novel approaches worth exploring",
    accent: "#c1272d",
  },
} as const;

// ── ROI Labels per tier ──
export const ROI_LABELS: Record<string, string> = {
  LOW_HANGING_FRUIT: "Proven ROI",
  MEDIUM_SOLUTION: "Adapted ROI",
  HARD_EXPERIMENT: "Estimated ROI",
};

// ── Evidence Tier Labels ──
export const EVIDENCE_TIER_LABELS: Record<string, string> = {
  DIRECT_MATCH: "Direct match",
  CALIBRATION_MATCH: "Calibration match",
  ADJACENT_MATCH: "Adjacent match",
};

// ── Report Sections (id, title, nav label) ──
export const REPORT_SECTIONS = [
  { id: "section-exec-summary", label: "Executive Summary" },
  { id: "section-current-state", label: "Current State" },
  { id: "section-use-cases", label: "Use Cases" },
  { id: "section-roi", label: "ROI Analysis" },
  { id: "section-roadmap", label: "Roadmap" },
] as const;

// ── Pipeline Stages (for landing page display) ──
export const PIPELINE_STAGES = [
  {
    num: "01",
    title: "SCRAPE",
    desc: "Fetches company pages, careers listings, and public content via HTTP",
  },
  {
    num: "02",
    title: "EXTRACT",
    desc: "LLM extracts AI readiness signals and classifies by dimension",
  },
  {
    num: "03",
    title: "SCORE",
    desc: "LLM scores maturity across four dimensions using extracted signals",
  },
  {
    num: "04",
    title: "MATCH",
    desc: "RAG retrieves similar engagements from the victory library",
  },
  {
    num: "05",
    title: "PRIORITIZE",
    desc: "LLM generates tiered use cases grounded in matched victories",
  },
  {
    num: "06",
    title: "REPORT",
    desc: "LLM writes five report sections in parallel",
  },
] as const;

// ── Agent Colors (for pipeline log) ──
export const AGENT_COLORS: Record<string, string> = {
  SCRAPE: "#1a1714",
  ANLYZ: "#6b5b4f",
  SCORE: "#c1272d",
  REPRT: "#2d6a4f",
};

// ── Fake Progress Entries ──
export interface FakeEntry {
  at: number;
  agent: string;
  message: string;
  done?: boolean;
}

export const FAKE_LOG_ENTRIES: FakeEntry[] = [
  { at: 0, agent: "SCRAPE", message: "Fetching company pages..." },
  { at: 6, agent: "SCRAPE", message: "Extracting page content..." },
  { at: 12, agent: "SCRAPE", message: "✓ Scrape complete", done: true },
  { at: 14, agent: "ANLYZ", message: "Analyzing signals from content..." },
  { at: 22, agent: "ANLYZ", message: "Classifying signal dimensions..." },
  { at: 30, agent: "ANLYZ", message: "✓ Signal extraction complete", done: true },
  { at: 32, agent: "SCORE", message: "Scoring AI maturity dimensions..." },
  { at: 40, agent: "SCORE", message: "Computing composite score..." },
  { at: 47, agent: "SCORE", message: "✓ Maturity scoring complete", done: true },
  { at: 49, agent: "REPRT", message: "Querying victory library..." },
  { at: 57, agent: "REPRT", message: "Generating use cases..." },
  { at: 65, agent: "REPRT", message: "Writing report sections..." },
] as const;

// ── Dimension Labels ──
export const DIMENSION_LABELS: { key: string; label: string }[] = [
  { key: "data_infrastructure", label: "Data Infrastructure" },
  { key: "ml_ai_capability", label: "ML / AI Capability" },
  { key: "strategy_intent", label: "Strategy & Intent" },
  { key: "operational_readiness", label: "Operational Readiness" },
];

// ── Data Flow Field Labels ──
export const DATA_FLOW_LABELS = [
  { label: "Inputs", field: "data_inputs" },
  { label: "Model", field: "model_approach" },
  { label: "Output", field: "output_consumer" },
  { label: "Feedback", field: "feedback_loop" },
  { label: "Measurement", field: "value_measurement" },
] as const;

// ── UI Layout Numbers ──
export const LAYOUT = {
  scrollOffset: 120,
  smoothScrollOffset: 80,
  logMaxHeight: 340,
  maxContentWidth: 920,
} as const;

// ── UI Strings ──
export const STRINGS = {
  siteName: "DISCOVERY AGENT",
  siteTitle: "AI Transformation Discovery Agent",
  siteDescription: "AI maturity assessment and transformation roadmap generator",
  kicker: "— AI-POWERED ANALYSIS",
  headline: "Enterprise AI readiness,",
  headlineItalic: "diagnosed in seconds",
  heroBody1:
    "Enter any company URL. A six-stage pipeline scrapes public data, extracts signals, scores AI maturity across four dimensions, matches against past engagements, and writes a transformation roadmap.",
  heroBody2:
    "Traditional discovery takes weeks and costs five figures. This runs in under two minutes.",
  pipelineTitle: "The Pipeline",
  beginAssessment: "Begin Assessment",
  analyzeCta: "Analyze \u2192",
  analyzing: "Analyzing...",
  dryRunLabel: "Dry run — use fixture data",
  dryRunMeta: "dry run is instant",
  placeholder: "https://stripe.com",
  pipelineExecution: "PIPELINE EXECUTION",
  initializing: "Initializing...",
  waitingForResponse: "Waiting for pipeline response...",
  analysisComplete: "✓ Analysis complete",
  newAnalysis: "New Analysis",
  recentAnalyses: "RECENT ANALYSES",
  clearHistory: "Clear history",
  supportingEvidence: "SUPPORTING EVIDENCE",
  pipelineTrace: "Pipeline Trace",
  traceSubtitle: "developer details",
  noRunId: "No run ID available.",
  traceUnavailable: "Trace data unavailable.",
  noStages: "No completed stages found.",
  maturityScoreLabel: "AI Maturity Score",
  dimensionsLabel: "Dimensions",
  confidence: "Confidence",
  dataFlow: "Data Flow",
  footerText: "Built for Tenex — AI transformation for the mid-market",
  footerMeta: "Multi-agent showcase",
} as const;

// ── Solutions Page Colors ──
export const INDUSTRY_BADGE_COLORS: Record<
  string,
  { bg: string; text: string; border: string }
> = {
  logistics: { bg: "#eff6ff", text: "#2563eb", border: "#bfdbfe" },
  financial_services: { bg: "#faf5ff", text: "#7c3aed", border: "#ddd6fe" },
  healthcare: { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
  retail: { bg: "#fdf4ff", text: "#a21caf", border: "#f0abfc" },
  manufacturing: { bg: "#fff7ed", text: "#c2410c", border: "#fed7aa" },
  default: { bg: "#f8fafc", text: "#475569", border: "#e2e8f0" },
};

export const SIZE_BADGE_COLORS: Record<string, { bg: string; text: string }> = {
  startup: { bg: "#f0fdf4", text: "#15803d" },
  "mid-market": { bg: "#fffbeb", text: "#b45309" },
  enterprise: { bg: "#eff6ff", text: "#1d4ed8" },
};

export const SOLUTIONS_ACCENT = {
  green: "#16a34a",
  darkText: "#1e2433",
  mutedText: "#4a5568",
  grayText: "#718096",
  metricBg: "#f0fdf4",
  metricBorder: "#bbf7d0",
  metricText: "#15803d",
  neutralBg: "#f8fafc",
  neutralText: "#475569",
  neutralBorder: "#e2e8f0",
  maturityBg: "#f1f5f9",
  maturityText: "#64748b",
} as const;
