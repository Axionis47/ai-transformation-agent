"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type { PageState, AnalyzeSuccess } from "@/lib/types";
import { parseApiError } from "@/lib/types";
import { saveAnalysis, getHistory, getAnalysis, clearHistory } from "@/lib/history";
import type { HistoryEntry } from "@/lib/history";
import ReportCard from "@/components/ReportCard";
import MaturityBadge from "@/components/MaturityBadge";
import PipelineProgress from "@/components/PipelineProgress";
import ErrorMessage from "@/components/ErrorMessage";
import URLInputForm from "@/components/URLInputForm";
import UseCaseTierSection from "@/components/UseCaseTierSection";
import TracePanel from "@/components/TracePanel";
import ReportNav from "@/components/ReportNav";
import UserHintsPanel from "@/components/UserHintsPanel";
import type { UserHintsPanelHandle } from "@/components/UserHintsPanel";
import MatchResultCard from "@/components/MatchResultCard";
import { API_BASE, scoreColor, STRINGS } from "@/lib/config";

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

function MatchResultsSection({ data }: { data: AnalyzeSuccess }) {
  const mr = data.match_results!;
  const shown = [
    ...mr.delivered.slice(0, 2),
    ...mr.adaptation.slice(0, 1),
    ...mr.ambitious.slice(0, 1),
  ];
  if (shown.length === 0) return null;
  return (
    <div>
      <p className="font-label uppercase tracking-[0.1em] text-xs text-ink-light mb-3">
        Victory Matches
        {data.has_user_hints && (
          <span className="ml-2 font-mono normal-case text-ink-faint">enhanced with your context</span>
        )}
      </p>
      {shown.map((r, i) => <MatchResultCard key={r.result_id ?? i} result={r} />)}
    </div>
  );
}

export default function AnalyzeForm() {
  const [state, setState] = useState<PageState>({ phase: "idle" });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const hintsRef = useRef<UserHintsPanelHandle>(null);

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
    const hints = hintsRef.current?.getHints() ?? null;
    try {
      const res = await fetch(`${API_BASE}/v1/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, dry_run: dryRun, ...(hints ? { user_hints: hints } : {}) }),
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
      <UserHintsPanel ref={hintsRef} />

      {state.phase === "loading" && <PipelineProgress onCancel={handleCancel} />}

      {state.phase === "error" && (
        <ErrorMessage message={state.message} onReset={() => setState({ phase: "idle" })} />
      )}

      {showHistory && (
        <div className="pt-2">
          <p className="font-label uppercase tracking-widest text-xs text-ink-light mb-3">
            {STRINGS.recentAnalyses}
          </p>
          <ul>
            {history.map((entry) => (
              <li key={entry.run_id} className="rule-hairline">
                <button
                  onClick={() => loadFromHistory(entry)}
                  className="w-full flex items-center gap-4 py-2.5 text-left hover:bg-red-light transition-colors focus:outline-none"
                >
                  <span className="font-mono text-xs text-ink-medium truncate flex-1">{entry.url}</span>
                  <span className="font-mono text-xs flex-shrink-0" style={{ color: scoreColor(entry.score) }}>
                    {entry.score.toFixed(1)}
                  </span>
                  <span className="font-mono text-xs text-ink-light flex-shrink-0">
                    {relativeDate(entry.date)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <button
            onClick={() => { clearHistory(); setHistory([]); }}
            className="font-body text-ink-light text-xs underline hover:text-ink transition-colors mt-3"
          >
            {STRINGS.clearHistory}
          </button>
        </div>
      )}

      {state.phase === "success" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <ReportNav />
            <button
              onClick={() => setState({ phase: "idle" })}
              className="font-label uppercase text-xs border border-ink bg-cream text-ink px-5 py-2 rounded-none transition-colors hover:bg-red hover:text-cream hover:border-red"
            >
              {STRINGS.newAnalysis}
            </button>
          </div>
          <MaturityBadge
            score={state.data.maturity.composite_score}
            label={state.data.maturity.composite_label}
            elapsedSeconds={state.data.elapsed_seconds}
            costUsd={state.data.cost_usd}
            dimensions={buildDimensions(state.data)}
          />
          {state.data.match_results && (
            <MatchResultsSection data={state.data} />
          )}
          <ReportCard
            id="section-exec-summary"
            title="Executive Summary"
            content={state.data.report.exec_summary}
            wins={state.data.victory_matches}
          />
          <ReportCard
            id="section-current-state"
            title="Current State"
            content={state.data.report.current_state}
          />
          {state.data.use_cases && state.data.use_cases.length > 0 ? (
            <UseCaseTierSection
              id="section-use-cases"
              useCases={state.data.use_cases}
            />
          ) : (
            <ReportCard
              id="section-use-cases"
              title="AI Use Cases"
              content={state.data.report.use_cases}
              wins={state.data.victory_matches}
            />
          )}
          <ReportCard
            id="section-roi"
            title="ROI Analysis"
            content={state.data.report.roi_analysis}
          />
          <ReportCard
            id="section-roadmap"
            title="Transformation Roadmap"
            content={state.data.report.roadmap}
          />
          <TracePanel runId={state.data.run_id} />
        </div>
      )}
    </div>
  );
}
