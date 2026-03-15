"use client";

import { useState } from "react";
import type { PageState, AnalyzeResponse, AnalyzeSuccess } from "@/lib/types";
import { ERROR_CODE_MAP } from "@/lib/types";
import ReportCard from "@/components/ReportCard";
import MaturityBadge from "@/components/MaturityBadge";
import PipelineProgress from "@/components/PipelineProgress";
import ErrorMessage from "@/components/ErrorMessage";
import URLInputForm from "@/components/URLInputForm";

const SECTION_LABELS: Record<string, string> = {
  exec_summary: "Executive Summary",
  current_state: "Current State",
  use_cases: "AI Use Cases",
  roadmap: "Transformation Roadmap",
  roi_analysis: "ROI Analysis",
};

const SECTION_ORDER = ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"] as const;

async function runAnalysis(url: string, dryRun: boolean): Promise<AnalyzeResponse> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${apiBase}/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, dry_run: dryRun }),
  });
  return res.json();
}

export default function AnalyzeForm() {
  const [state, setState] = useState<PageState>({ phase: "idle" });

  async function handleSubmit(url: string, dryRun: boolean) {
    setState({ phase: "loading" });
    try {
      const json = await runAnalysis(url, dryRun);
      if (json.status === "failed") {
        const code = "error" in json ? (json.error?.code ?? "UNKNOWN") : "UNKNOWN";
        setState({ phase: "error", message: ERROR_CODE_MAP[code] ?? "Unknown error." });
        return;
      }
      setState({ phase: "success", data: json as AnalyzeSuccess });
    } catch {
      setState({ phase: "error", message: "Could not reach the analysis server. Is it running?" });
    }
  }

  return (
    <div className="space-y-8">
      <URLInputForm onSubmit={handleSubmit} isLoading={state.phase === "loading"} />
      {state.phase === "loading" && <PipelineProgress />}
      {state.phase === "error" && (
        <ErrorMessage message={state.message} onReset={() => setState({ phase: "idle" })} />
      )}
      {state.phase === "success" && (
        <div className="space-y-6">
          <MaturityBadge
            score={state.data.analysis?.maturity_score}
            label={state.data.analysis?.maturity_label}
            elapsedSeconds={state.data.elapsed_seconds}
            costUsd={state.data.cost_usd}
            dimensions={state.data.analysis?.dimensions}
          />
          {SECTION_ORDER.map((key) => (
            <ReportCard
              key={key}
              title={SECTION_LABELS[key]}
              content={state.data.report[key]}
              wins={state.data.rag_context}
            />
          ))}
        </div>
      )}
    </div>
  );
}
