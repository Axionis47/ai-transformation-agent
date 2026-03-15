export interface VictoryMatch {
  id: string;
  engagement_title: string;
  industry: string;
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

// Human-readable error code map — lives in frontend, not backend
export const ERROR_CODE_MAP: Record<string, string> = {
  SCRAPE_FAIL: "Could not reach that website. Try a different URL.",
  SCRAPE_THIN: "The website had too little content to analyze. Try the company's main page.",
  RAG_ERROR: "Failed to find comparable companies. The analysis may be less complete.",
  CONSULTANT_ERROR: "Scoring agent encountered an error. Please retry.",
  REPORT_ERROR: "Report generation failed. Please retry.",
  UNKNOWN: "An unexpected error occurred. Please retry.",
};
