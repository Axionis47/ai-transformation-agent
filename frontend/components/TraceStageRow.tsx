"use client";

import { useState } from "react";

export interface TraceStage {
  agent_tag: string;
  event: string;
  latency_ms: number;
  prompt_file: string | null;
  prompt_version: string | null;
  input_summary: Record<string, unknown>;
  output_summary: Record<string, unknown>;
  timestamp: string;
}

interface TraceStageRowProps {
  stage: TraceStage;
}

function formatLatency(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

function SummaryTable({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <p className="text-gray-400 italic text-xs">No data</p>;
  }
  return (
    <dl className="space-y-1.5">
      {entries.map(([key, value]) => (
        <div key={key} className="flex gap-2 text-xs">
          <dt className="text-gray-400 font-mono min-w-[110px] shrink-0">{key}</dt>
          <dd className="text-gray-500 break-all">{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function TraceStageRow({ stage }: TraceStageRowProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-[#c4cad6]/40 bg-[#f4f6fa] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between gap-3 text-left px-4 py-3 hover:bg-[#edf0f5] transition-colors"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="font-mono text-xs font-bold text-gray-600 shrink-0 bg-gray-200 px-2 py-0.5 rounded">
            {stage.agent_tag}
          </span>
          <span
            className="text-[11px] font-mono px-2 py-0.5 rounded"
            style={{ background: "#e0e7ff", color: "#4f6df5" }}
          >
            {formatLatency(stage.latency_ms)}
          </span>
          {stage.prompt_file && (
            <span className="text-[11px] text-gray-400 truncate">
              {stage.prompt_file}
              {stage.prompt_version && (
                <span className="ml-1 text-gray-300">v{stage.prompt_version}</span>
              )}
            </span>
          )}
        </div>
        <span
          className="text-gray-400 text-xs shrink-0 transition-transform duration-200"
          style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
        >
          ▾
        </span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-3 border-t border-[#c4cad6]/30 grid grid-cols-2 gap-6">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2">
              Input
            </p>
            <SummaryTable data={stage.input_summary} />
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2">
              Output
            </p>
            <SummaryTable data={stage.output_summary} />
          </div>
        </div>
      )}
    </div>
  );
}
