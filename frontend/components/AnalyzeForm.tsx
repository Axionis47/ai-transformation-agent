"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type { PageState, AnalyzeSuccess } from "@/lib/types";
import { parseApiError } from "@/lib/types";
import { saveAnalysis, getHistory, getAnalysis } from "@/lib/history";
import type { HistoryEntry } from "@/lib/history";
import ReportCard from "@/components/ReportCard";
import MaturityBadge from "@/components/MaturityBadge";
import PipelineProgress from "@/components/PipelineProgress";
import ErrorMessage from "@/components/ErrorMessage";
import URLInputForm from "@/components/URLInputForm";
import UseCaseTierSection from "@/components/UseCaseTierSection";
import TracePanel from "@/components/TracePanel";

function buildDimensions(data: AnalyzeSuccess): Record<string, number> | undefined {
  if (data.maturity?.dimensions) {
    return Object.fromEntries(
      Object.entries(data.maturity.dimensions).map(([k, v]) => [k, v.score])
    );
  }
  return undefined;
}

function relativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function scoreBadgeStyle(score: number): { bg: string; text: string } {
  if (score >= 4) return { bg: "#e8f0fe", text: "#3b5de7" };
  if (score >= 2.5) return { bg: "#fef9e7", text: "#b7791f" };
  return { bg: "#fdecea", text: "#c0392b" };
}

export default function AnalyzeForm() {
  const [state, setState] = useState<PageState>({ phase: "idle" });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setState({ phase: "idle" });
  }, []);

  async function handleSubmit(url: string, dryRun: boolean) {
    const controller = new AbortController();
    abortRef.current = controller;
    setState({ phase: "loading" });
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res = await fetch(`${apiBase}/v1/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, dry_run: dryRun }),
        signal: controller.signal,
      });
      const body = await res.json();
      if (!res.ok) {
        setState({ phase: "error", message: parseApiError(body) });
        return;
      }
      const data = body as Record<string, unknown>;
      if (data["status"] === "failed") {
        setState({ phase: "error", message: parseApiError(body) });
        return;
      }
      const result = body as AnalyzeSuccess;
      saveAnalysis(url, result);
      setHistory(getHistory());
      setState({ phase: "success", data: result });
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setState({ phase: "idle" });
        return;
      }
      setState({ phase: "error", message: "Could not reach the analysis server. Is it running?" });
    }
  }

  function loadFromHistory(entry: HistoryEntry) {
    const data = getAnalysis(entry.run_id);
    if (data) setState({ phase: "success", data });
  }

  const showHistory = state.phase === "idle" && history.length > 0;

  return (
    <div className="space-y-8">
      <URLInputForm onSubmit={handleSubmit} isLoading={state.phase === "loading"} />

      {state.phase === "loading" && <PipelineProgress onCancel={handleCancel} />}

      {state.phase === "error" && (
        <ErrorMessage message={state.message} onReset={() => setState({ phase: "idle" })} />
      )}

      {showHistory && (
        <div className="neo-flat p-5 space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400">
            Recent Analyses
          </h2>
          <ul className="space-y-2">
            {history.map((entry) => {
              const badge = scoreBadgeStyle(entry.score);
              return (
                <li key={entry.run_id}>
                  <button
                    onClick={() => loadFromHistory(entry)}
                    className="w-full neo-flat px-4 py-3 rounded-xl flex items-center justify-between gap-3 text-left hover:shadow-neo-btn-pressed transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4f6df5]"
                  >
                    <span className="text-sm text-gray-700 truncate flex-1">{entry.url}</span>
                    <span
                      className="flex-shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{ background: badge.bg, color: badge.text }}
                    >
                      {entry.score.toFixed(1)} &middot; {entry.label}
                    </span>
                    <span className="flex-shrink-0 text-xs text-gray-400">
                      {relativeDate(entry.date)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {state.phase === "success" && (
        <div className="space-y-6">
          <div className="flex justify-end">
            <button
              onClick={() => setState({ phase: "idle" })}
              className="neo-flat px-5 py-2 text-xs font-medium text-gray-500 rounded-xl transition-all hover:text-gray-700 active:shadow-neo-btn-pressed focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4f6df5]"
            >
              + New Analysis
            </button>
          </div>
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
