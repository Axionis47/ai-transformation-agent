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

// Human-readable error code map — lives in frontend, not backend
export const ERROR_CODE_MAP: Record<string, string> = {
  SCRAPE_FAIL: "Could not reach that website. Try a different URL.",
  SCRAPE_THIN: "The website had too little content to analyze. Try the company's main page.",
  RAG_ERROR: "Failed to find comparable companies. The analysis may be less complete.",
  CONSULTANT_ERROR: "Scoring agent encountered an error. Please retry.",
  REPORT_ERROR: "Report generation failed. Please retry.",
  UNKNOWN: "An unexpected error occurred. Please retry.",
};
