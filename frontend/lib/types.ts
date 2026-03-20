export interface Signal {
  signal_id: string;
  type: string;
  value: string;
  source: string;
  confidence: number;
  raw_quote: string;
}

export interface SignalSet {
  signals: Signal[];
  industry: string;
  scale: string;
  confidence_level: "HIGH" | "MEDIUM" | "LOW";
  signal_count: number;
}

export interface DimensionScore {
  score: number;
  signals_used: string[];
  rationale: string;
}

export interface MaturityResult {
  dimensions: Record<string, DimensionScore>;
  composite_score: number;
  composite_label: string;
  composite_rationale: string;
}

export interface DataFlow {
  data_inputs: string[];
  model_approach: string;
  output_consumer: string;
  feedback_loop: string;
  value_measurement: string;
}

export interface TieredUseCase {
  tier: "LOW_HANGING_FRUIT" | "MEDIUM_SOLUTION" | "HARD_EXPERIMENT";
  title: string;
  description: string;
  evidence_signal_ids: string[];
  effort: "Low" | "Medium" | "High";
  impact: "Low" | "Medium" | "High";
  roi_estimate: string;
  roi_basis: string;
  rag_benchmark: string | null;
  confidence: number;
  why_this_company: string;
  data_flow: DataFlow;
  // DELIVERED tier (LOW_HANGING_FRUIT) — tier-specific evidence fields
  win_id?: string;
  client_profile_match?: string;
  proven_metric?: string;
  // ADAPTATION tier (MEDIUM_SOLUTION) — tier-specific evidence fields
  base_win_id?: string;
  adaptation_notes?: string;
  adjusted_roi_range?: string;
  // AMBITIOUS tier (HARD_EXPERIMENT) — tier-specific evidence fields
  industry_examples?: string[];
  source_citations?: string[];
}

export interface VictoryMatch {
  win_id: string;
  engagement_title: string;
  match_tier: "DIRECT_MATCH" | "CALIBRATION_MATCH" | "ADJACENT_MATCH";
  relevance_note: string;
  roi_benchmark: string;
  industry: string;
  similarity_score: number;
  confidence: number;
  gap_analysis?: string;
}

export interface UserHints {
  pain_points: string[];
  known_tech: string[];
  industry: string;
  employee_count: number | null;
  context: string;
}

export interface ConfidenceBreakdown {
  industry_match: number;
  pain_point_match: number;
  tech_feasibility: number;
  scale_match: number;
  maturity_fit: number;
  evidence_depth: number;
  evidence_ceiling: "url_only" | "url_plus_hints" | "confirmed";
  overall: number;
  explanation: string;
}

export interface MatchResult {
  result_id: string;
  match_tier: "DELIVERED" | "ADAPTATION" | "AMBITIOUS";
  confidence: number;
  confidence_breakdown?: ConfidenceBreakdown;
  source_id: string;
  source_title: string;
  source_industry: string;
  relevance_note: string;
  proven_metrics?: {
    primary_label: string;
    primary_value: string;
    measurement_period: string;
  };
  gap_analysis?: string;
}

export interface ReportSections {
  exec_summary: string;
  current_state: string;
  use_cases: string;
  roadmap: string;
  roi_analysis: string;
}

export interface AnalyzeSuccess {
  run_id: string;
  status: "complete";
  elapsed_seconds: number;
  cost_usd: number;
  report: ReportSections;
  maturity: MaturityResult;
  signals?: SignalSet;
  victory_matches?: VictoryMatch[];
  use_cases?: TieredUseCase[];
  match_results?: {
    delivered: MatchResult[];
    adaptation: MatchResult[];
    ambitious: MatchResult[];
  };
  has_user_hints?: boolean;
  pitch_brief?: {
    opening_line: string;
    story: string;
    roi_conversation: string;
    questions: string[];
    objection_prep: string;
  };
  readiness?: {
    score: number;
    label: string;
    components: Record<string, number>;
    next_action: string;
  };
  suggested_questions?: Array<{
    question: string;
    dimension: string;
    potential_lift: number;
    why: string;
  }>;
  // backward compat — present in older responses
  analysis?: {
    maturity_score?: number;
    maturity_label?: string;
    dimensions?: Record<string, unknown>;
    use_cases?: unknown[];
  };
  rag_context?: VictoryMatch[];
  pages_fetched?: string[];
  signal_count?: number;
}

// Backend wraps errors as: { "detail": { "error": { code, message, agent } } }
export interface AnalyzeErrorBody {
  detail: {
    error: {
      code: string;
      message: string;
      agent: string;
    };
  };
}

export interface AnalyzeError {
  run_id?: string;
  status: "failed";
  error: {
    code: string;
    message: string;
    agent: string;
  };
}

export type AnalyzeResponse = AnalyzeSuccess | AnalyzeError;

export type PageState =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "success"; data: AnalyzeSuccess }
  | { phase: "error"; message: string };

export const ERROR_CODE_MAP: Record<string, string> = {
  SCRAPE_FAIL: "Could not reach that website. Try a different URL.",
  SCRAPE_THIN: "The website had too little content to analyze. Try the company's main page.",
  RAG_ERROR: "Failed to find comparable companies. The analysis may be less complete.",
  CONSULTANT_ERROR: "Scoring agent encountered an error. Please retry.",
  REPORT_ERROR: "Report generation failed. Please retry.",
  UNKNOWN: "An unexpected error occurred. Please retry.",
};

/**
 * Parse an error response from the backend.
 * Backend sends 422/500 with body: { detail: { error: { code, message, agent } } }
 * Falls back gracefully if the shape is unexpected.
 */
export function parseApiError(body: unknown): string {
  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>;
    // Structured error: { detail: { error: { code, message } } }
    const detail = b["detail"];
    if (detail && typeof detail === "object") {
      const d = detail as Record<string, unknown>;
      const err = d["error"];
      if (err && typeof err === "object") {
        const e = err as Record<string, unknown>;
        const code = typeof e["code"] === "string" ? e["code"] : "UNKNOWN";
        return ERROR_CODE_MAP[code] ?? String(e["message"] ?? "Unknown error.");
      }
    }
    // Flat error: { status: "failed", error: { code } }
    const err = b["error"];
    if (err && typeof err === "object") {
      const e = err as Record<string, unknown>;
      const code = typeof e["code"] === "string" ? e["code"] : "UNKNOWN";
      return ERROR_CODE_MAP[code] ?? String(e["message"] ?? "Unknown error.");
    }
  }
  return ERROR_CODE_MAP["UNKNOWN"];
}
