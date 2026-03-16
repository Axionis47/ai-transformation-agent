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
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  return `${ms}ms`;
}

function SummaryTable({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <p className="text-gray-400 italic text-xs">No data</p>;
  }
  return (
    <dl className="space-y-1">
      {entries.map(([key, value]) => (
        <div key={key} className="flex gap-2 text-xs">
          <dt className="text-gray-400 font-mono min-w-[120px] shrink-0">{key}</dt>
          <dd className="text-gray-600 break-all">{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function TraceStageRow({ stage }: TraceStageRowProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="neo-flat p-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between gap-3 text-left"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="font-mono font-semibold text-gray-700 text-sm shrink-0">
            {stage.agent_tag}
          </span>
          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-mono shrink-0">
            {formatLatency(stage.latency_ms)}
          </span>
          {stage.prompt_file && (
            <span className="text-xs text-gray-400 truncate">
              {stage.prompt_file}
              {stage.prompt_version && (
                <span className="ml-1 text-gray-300">v{stage.prompt_version}</span>
              )}
            </span>
          )}
        </div>
        <span className="text-gray-400 text-xs shrink-0">{expanded ? "▾" : "▸"}</span>
      </button>

      {expanded && (
        <div className="mt-3 grid grid-cols-2 gap-4 pt-3 border-t border-neo-dark/20">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">
              Input
            </p>
            <SummaryTable data={stage.input_summary} />
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">
              Output
            </p>
            <SummaryTable data={stage.output_summary} />
          </div>
        </div>
      )}
    </div>
  );
}
