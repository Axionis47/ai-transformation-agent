// ---------------------------------------------------------------------------
// Centralized constants for the frontend application.
// Organized by domain. Import from "@/config/constants" everywhere.
// ---------------------------------------------------------------------------

// -- Pipeline phases --------------------------------------------------------

export const PHASES = [
  "INTAKE",
  "GROUNDING",
  "DEEP_RESEARCH",
  "HYPOTHESIS_FORMATION",
  "HYPOTHESIS_TESTING",
  "SYNTHESIS",
  "REVIEW",
  "PUBLISHED",
];

export const ACTIVE_PHASES = [
  "grounding",
  "deep_research",
  "hypothesis_formation",
  "hypothesis_testing",
  "synthesis",
];

export const AGENT_PHASES = ["grounding", "deep_research", "hypothesis_formation", "hypothesis_testing"];

export const HYPOTHESIS_PHASES = ["hypothesis_formation", "hypothesis_testing"];

export const TERMINAL = ["review", "published", "failed"];

export const STAGE_ORDER = [
  "created",
  "intake",
  "assumptions_draft",
  "assumptions_confirmed",
  "reasoning",
  "synthesis",
  "report",
  "published",
];

// -- Polling & timeouts -----------------------------------------------------

/** Polling interval (ms) for the run dashboard during active phases. */
export const POLL_INTERVAL_MS = 2000;

/** Delay (ms) before clearing the "last edited" highlight on report feedback. */
export const FEEDBACK_HIGHLIGHT_MS = 3000;

/** Max characters shown when rendering a JSON trace payload. */
export const TRACE_JSON_TRUNCATE = 2000;

// -- Tier display maps (report page) ---------------------------------------

export const TIER_BORDER: Record<string, string> = {
  easy: "border-l-mint",
  medium: "border-l-amber",
  hard: "border-l-rose",
};

export const TIER_VARIANT: Record<string, "mint" | "amber" | "rose"> = {
  easy: "mint",
  medium: "amber",
  hard: "rose",
};

export const TIER_LABEL: Record<string, string> = {
  easy: "Quick Win",
  medium: "Strategic Initiative",
  hard: "Transformation",
};

export const TIER_TIMELINE: Record<string, string> = {
  easy: "4-6 weeks",
  medium: "2-3 months",
  hard: "6+ months",
};

// -- Trace page maps -------------------------------------------------------

export const PHASE_COLORS: Record<string, string> = {
  grounding: "text-indigo",
  deep_research: "text-amber",
  hypothesis_formation: "text-amber",
  hypothesis_testing: "text-mint",
  synthesis: "text-mint",
  review: "text-mint",
};

export const EVENT_LABELS: Record<string, string> = {
  // Multi-agent events
  AGENT_SPAWNED: "Agent Spawned",
  AGENT_COMPLETED: "Agent Completed",
  AGENT_FAILED: "Agent Failed",
  HYPOTHESIS_FORMED: "Hypothesis Formed",
  HYPOTHESIS_TESTED: "Hypothesis Tested",
  HYPOTHESIS_VALIDATED: "Hypothesis Validated",
  HYPOTHESIS_REJECTED: "Hypothesis Rejected",
  USER_INTERACTION_SURFACED: "User Interaction",
  USER_INTERACTION_RESOLVED: "Interaction Resolved",
  SPAWN_REQUESTED: "Spawn Requested",
  PHASE_BACKTRACK: "Phase Backtrack",
  REPORT_STRUCTURE_DECIDED: "Report Structured",
  // Evidence & tools
  GROUNDING_CALL_REQUESTED: "Google Search",
  GROUNDING_CALL_COMPLETED: "Ground Result",
  GROUNDING_QUERIES_COUNTED: "Search Budget",
  RAG_QUERY_EXECUTED: "KB Search",
  RAG_RESULTS_FILTERED: "KB Cross-ref",
  EVIDENCE_PROMOTED: "Evidence Stored",
  EVIDENCE_REJECTED: "Evidence Rejected",
  EVIDENCE_CONTRADICTION: "Evidence Conflict",
  // Budget & errors
  EXTERNAL_BUDGET_EXHAUSTED: "Budget Exhausted",
  BUDGET_VIOLATION_BLOCKED: "Budget Blocked",
  STAGE_FAILED: "Stage Failed",
  // Lifecycle
  RUN_CREATED: "Run Created",
  COMPANY_INTAKE_SAVED: "Intake Saved",
  REASONING_LOOP_STARTED: "Loop Started",
  REASONING_LOOP_COMPLETED: "Loop Completed",
  REPORT_RENDERED: "Report Rendered",
  REPORT_REFINED: "Report Refined",
  RUN_PUBLISHED: "Published",
};

export const AGENT_TYPE_LABELS: Record<string, string> = {
  company_profiler: "Company Profiler",
  industry_analyst: "Industry Analyst",
  pain_investigator: "Pain Investigator",
  hypothesis_former: "Hypothesis Former",
  hypothesis_tester: "Hypothesis Tester",
  report_synthesizer: "Report Synthesizer",
};

export const FILTERS = ["all", "agents", "hypotheses", "evidence", "budget"] as const;

// -- Form options -----------------------------------------------------------

export const ENRICHMENT_CATEGORIES: { value: import("@/lib/types").EnrichmentCategory; label: string }[] = [
  { value: "technology", label: "Technology & Systems" },
  { value: "financials", label: "Financials & Budget" },
  { value: "operations", label: "Operations & Processes" },
  { value: "pain_points", label: "Pain Points" },
  { value: "constraints", label: "Constraints & Blockers" },
  { value: "corrections", label: "Corrections (tried & failed)" },
  { value: "additional_context", label: "Additional Context" },
];

export const SIZE_OPTIONS = ["50-100", "100-200", "200-500", "500-2000", "2000+"];
