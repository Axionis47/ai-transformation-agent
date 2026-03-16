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
    <div className="neo-raised p-5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 text-left"
        aria-expanded={open}
      >
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-widest">
          Pipeline Trace
        </h2>
        <span className="text-gray-400 text-sm">{open ? "▾" : "▸"}</span>
      </button>

      {open && (
        <div className="mt-4 space-y-2">
          {!runId && (
            <p className="text-sm text-gray-400 text-center py-4">
              No run ID available.
            </p>
          )}

          {runId && fetchState.status === "loading" && (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="neo-flat p-4 animate-pulse h-12 rounded-neo"
                />
              ))}
            </div>
          )}

          {runId && fetchState.status === "error" && (
            <p className="text-sm text-gray-400 text-center py-4">
              Trace data unavailable.
            </p>
          )}

          {runId && fetchState.status === "success" && completeStages.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-4">
              No completed stages found.
            </p>
          )}

          {runId && fetchState.status === "success" && completeStages.length > 0 && (
            <div className="space-y-2">
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
