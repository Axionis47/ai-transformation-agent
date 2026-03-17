"use client";

import { useState } from "react";
import type { PageState, AnalyzeSuccess } from "@/lib/types";
import { parseApiError } from "@/lib/types";
import ReportCard from "@/components/ReportCard";
import MaturityBadge from "@/components/MaturityBadge";
import PipelineProgress from "@/components/PipelineProgress";
import ErrorMessage from "@/components/ErrorMessage";
import URLInputForm from "@/components/URLInputForm";
import UseCaseTierSection from "@/components/UseCaseTierSection";
import TracePanel from "@/components/TracePanel";

async function runAnalysis(url: string, dryRun: boolean): Promise<{ ok: boolean; body: unknown }> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${apiBase}/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, dry_run: dryRun }),
  });
  const body = await res.json();
  return { ok: res.ok, body };
}

function buildDimensions(data: AnalyzeSuccess): Record<string, number> | undefined {
  if (data.maturity?.dimensions) {
    return Object.fromEntries(
      Object.entries(data.maturity.dimensions).map(([k, v]) => [k, v.score])
    );
  }
  return undefined;
}

export default function AnalyzeForm() {
  const [state, setState] = useState<PageState>({ phase: "idle" });

  async function handleSubmit(url: string, dryRun: boolean) {
    setState({ phase: "loading" });
    try {
      const { ok, body } = await runAnalysis(url, dryRun);
      if (!ok) {
        setState({ phase: "error", message: parseApiError(body) });
        return;
      }
      const data = body as Record<string, unknown>;
      if (data["status"] === "failed") {
        setState({ phase: "error", message: parseApiError(body) });
        return;
      }
      setState({ phase: "success", data: body as AnalyzeSuccess });
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
            score={state.data.maturity.composite_score}
            label={state.data.maturity.composite_label}
            elapsedSeconds={state.data.elapsed_seconds}
            costUsd={state.data.cost_usd}
            dimensions={buildDimensions(state.data)}
          />
          <ReportCard
            title="Executive Summary"
            content={state.data.report.exec_summary}
            wins={state.data.victory_matches}
          />
          <ReportCard title="Current State" content={state.data.report.current_state} />
          {state.data.use_cases && state.data.use_cases.length > 0 ? (
            <UseCaseTierSection useCases={state.data.use_cases} />
          ) : (
            <ReportCard
              title="AI Use Cases"
              content={state.data.report.use_cases}
              wins={state.data.victory_matches}
            />
          )}
          <ReportCard title="ROI Analysis" content={state.data.report.roi_analysis} />
          <ReportCard title="Transformation Roadmap" content={state.data.report.roadmap} />
          <TracePanel runId={state.data.run_id} />
        </div>
      )}
    </div>
  );
}
