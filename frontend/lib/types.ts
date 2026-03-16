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
}

export interface VictoryMatch {
  win_id: string;
  id?: string;
  engagement_title: string;
  match_tier: "DIRECT_MATCH" | "CALIBRATION_MATCH" | "ADJACENT_MATCH";
  relevance_note?: string;
  roi_benchmark: string;
  industry: string;
  similarity_score?: number;
  confidence: number;
  size_label?: string;
  primary_metric_label?: string;
  primary_metric_value?: string;
  measurement_period?: string;
  duration_months?: number;
  maturity_at_engagement?: string;
  embed_text?: string;
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
  analysis?: {
    maturity_score?: number;
    maturity_label?: string;
    dimensions?: {
      data_infrastructure?: number;
      ml_ai_capability?: number;
      strategy_intent?: number;
      operational_readiness?: number;
    };
    [key: string]: unknown;
  };
  rag_context?: VictoryMatch[];
  signals?: SignalSet;
  maturity?: MaturityResult;
  victory_matches?: VictoryMatch[];
  use_cases?: TieredUseCase[];
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
