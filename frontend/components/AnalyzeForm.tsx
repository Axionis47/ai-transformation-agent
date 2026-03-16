"use client";

import { useState } from "react";
import type { PageState, AnalyzeResponse, AnalyzeSuccess } from "@/lib/types";
import { ERROR_CODE_MAP } from "@/lib/types";
import ReportCard from "@/components/ReportCard";
import MaturityBadge from "@/components/MaturityBadge";
import PipelineProgress from "@/components/PipelineProgress";
import ErrorMessage from "@/components/ErrorMessage";
import URLInputForm from "@/components/URLInputForm";
import UseCaseTierSection from "@/components/UseCaseTierSection";
import TracePanel from "@/components/TracePanel";

async function runAnalysis(url: string, dryRun: boolean): Promise<AnalyzeResponse> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${apiBase}/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, dry_run: dryRun }),
  });
  return res.json();
}

function buildDimensions(data: AnalyzeSuccess): Record<string, number> | undefined {
  if (data.maturity?.dimensions) {
    return Object.fromEntries(
      Object.entries(data.maturity.dimensions).map(([k, v]) => [k, v.score])
    );
  }
  return data.analysis?.dimensions;
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
            score={state.data.maturity?.composite_score ?? state.data.analysis?.maturity_score}
            label={state.data.maturity?.composite_label ?? state.data.analysis?.maturity_label}
            elapsedSeconds={state.data.elapsed_seconds}
            costUsd={state.data.cost_usd}
            dimensions={buildDimensions(state.data)}
          />
          <ReportCard title="Executive Summary" content={state.data.report.exec_summary} wins={state.data.victory_matches ?? state.data.rag_context} />
          <ReportCard title="Current State" content={state.data.report.current_state} />
          {state.data.use_cases && state.data.use_cases.length > 0 ? (
            <UseCaseTierSection useCases={state.data.use_cases} />
          ) : (
            <ReportCard title="AI Use Cases" content={state.data.report.use_cases} wins={state.data.victory_matches ?? state.data.rag_context} />
          )}
          <ReportCard title="ROI Analysis" content={state.data.report.roi_analysis} />
          <ReportCard title="Transformation Roadmap" content={state.data.report.roadmap} />
          <TracePanel runId={state.data.run_id} />
        </div>
      )}
    </div>
  );
}
