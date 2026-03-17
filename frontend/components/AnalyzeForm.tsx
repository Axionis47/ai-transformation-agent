"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { PageState, AnalyzeSuccess } from "@/lib/types";
import { parseApiError } from "@/lib/types";
import { saveAnalysis, getHistory } from "@/lib/history";
import type { HistoryEntry } from "@/lib/history";
import PipelineProgress from "@/components/PipelineProgress";
import ErrorMessage from "@/components/ErrorMessage";
import URLInputForm from "@/components/URLInputForm";

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
  const router = useRouter();
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
      router.push(`/analysis/${result.run_id}`);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setState({ phase: "idle" });
        return;
      }
      setState({ phase: "error", message: "Could not reach the analysis server. Is it running?" });
    }
  }

  function loadFromHistory(entry: HistoryEntry) {
    router.push(`/analysis/${entry.run_id}`);
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

    </div>
  );
}
