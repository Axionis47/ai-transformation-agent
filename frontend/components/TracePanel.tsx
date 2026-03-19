"use client";

import { useState, useEffect } from "react";
import TraceStageRow from "@/components/TraceStageRow";
import type { TraceStage } from "@/components/TraceStageRow";

interface TraceResponse {
  run_id: string;
  stages: TraceStage[];
}

interface TracePanelProps {
  runId: string | null;
}

type FetchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: TraceResponse }
  | { status: "error" };

async function fetchTrace(runId: string): Promise<TraceResponse> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${apiBase}/v1/trace/${runId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export default function TracePanel({ runId }: TracePanelProps) {
  const [open, setOpen] = useState(false);
  const [fetchState, setFetchState] = useState<FetchState>({ status: "idle" });

  useEffect(() => {
    if (!open || !runId) return;
    if (fetchState.status === "success" || fetchState.status === "loading") return;

    setFetchState({ status: "loading" });
    fetchTrace(runId)
      .then((data) => setFetchState({ status: "success", data }))
      .catch(() => setFetchState({ status: "error" }));
  }, [open, runId]); // eslint-disable-line react-hooks/exhaustive-deps

  const completeStages =
    fetchState.status === "success"
      ? fetchState.data.stages.filter((s) => s.event === "agent_complete")
      : [];

  return (
    <div style={{ borderTop: "1px solid var(--ink)" }}>
      {/* Toggle header */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 text-left py-3 group"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <span className="font-label text-xs uppercase tracking-[0.12em] text-ink-light group-hover:text-ink-medium transition-colors">
            Pipeline Trace
          </span>
          <span className="font-label text-xs text-ink-faint">developer details</span>
        </div>
        <span
          className="text-ink-light text-xs transition-transform duration-200"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div className="pb-6 pt-1 space-y-0">
          {!runId && (
            <p className="font-body text-xs text-ink-faint py-4 text-center">
              No run ID available.
            </p>
          )}

          {runId && fetchState.status === "loading" && (
            <div className="space-y-2 pt-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-8 animate-pulse"
                  style={{ background: "var(--rule)" }}
                />
              ))}
            </div>
          )}

          {runId && fetchState.status === "error" && (
            <p className="font-body text-xs text-ink-faint py-4 text-center">
              Trace data unavailable.
            </p>
          )}

          {runId && fetchState.status === "success" && completeStages.length === 0 && (
            <p className="font-body text-xs text-ink-faint py-4 text-center">
              No completed stages found.
            </p>
          )}

          {runId && fetchState.status === "success" && completeStages.length > 0 && (
            <div>
              {completeStages.map((stage, i) => (
                <TraceStageRow key={`${stage.agent_tag}-${i}`} stage={stage} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
