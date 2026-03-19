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
    return <p className="font-body text-xs text-ink-faint italic">No data</p>;
  }
  return (
    <dl className="space-y-1.5">
      {entries.map(([key, value]) => (
        <div key={key} className="flex gap-3 text-xs">
          <dt className="font-mono text-ink-light min-w-[110px] shrink-0">{key}</dt>
          <dd className="font-body text-ink-medium break-all">{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function TraceStageRow({ stage }: TraceStageRowProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{ borderBottom: "0.5px solid var(--rule)" }}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between gap-3 text-left py-3 group"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3 min-w-0 flex-wrap">
          <span
            className="font-mono font-bold text-xs text-ink px-2 py-0.5 shrink-0"
            style={{ background: "var(--red-light)" }}
          >
            {stage.agent_tag}
          </span>
          <span className="font-mono text-xs text-red shrink-0">
            {formatLatency(stage.latency_ms)}
          </span>
          {stage.prompt_file && (
            <span className="font-mono text-xs text-ink-light truncate">
              {stage.prompt_file}
              {stage.prompt_version && (
                <span className="ml-1 text-ink-faint">v{stage.prompt_version}</span>
              )}
            </span>
          )}
        </div>
        <span
          className="text-ink-light text-xs shrink-0 transition-transform duration-200"
          style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
        >
          ▾
        </span>
      </button>

      {expanded && (
        <div className="pb-4 pt-2 grid grid-cols-2 gap-6">
          <div>
            <p className="font-label text-xs uppercase tracking-[0.1em] text-ink-light mb-2">
              Input
            </p>
            <SummaryTable data={stage.input_summary} />
          </div>
          <div>
            <p className="font-label text-xs uppercase tracking-[0.1em] text-ink-light mb-2">
              Output
            </p>
            <SummaryTable data={stage.output_summary} />
          </div>
        </div>
      )}
    </div>
  );
}
