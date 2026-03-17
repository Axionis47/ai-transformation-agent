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
    <div className="rounded-2xl border border-[#c4cad6]/40 bg-[#f4f6fa] overflow-hidden">
      {/* Toggle header — muted, unobtrusive */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 text-left px-5 py-3.5 hover:bg-[#edf0f5] transition-colors"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2.5">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">
            Pipeline Trace
          </span>
          <span className="text-[10px] text-gray-300">— developer details</span>
        </div>
        <span
          className="text-gray-400 text-xs transition-transform duration-200"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div className="px-5 pb-5 pt-1 border-t border-[#c4cad6]/30 space-y-2">
          {!runId && (
            <p className="text-xs text-gray-400 py-4 text-center">No run ID available.</p>
          )}

          {runId && fetchState.status === "loading" && (
            <div className="space-y-2 pt-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-11 rounded-xl bg-gray-200 animate-pulse" />
              ))}
            </div>
          )}

          {runId && fetchState.status === "error" && (
            <p className="text-xs text-gray-400 py-4 text-center">Trace data unavailable.</p>
          )}

          {runId && fetchState.status === "success" && completeStages.length === 0 && (
            <p className="text-xs text-gray-400 py-4 text-center">No completed stages found.</p>
          )}

          {runId && fetchState.status === "success" && completeStages.length > 0 && (
            <div className="space-y-2 pt-2">
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
