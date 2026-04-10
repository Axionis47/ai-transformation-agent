import {
  EVENT_LABELS,
  AGENT_TYPE_LABELS,
  PHASE_COLORS,
  TRACE_JSON_TRUNCATE,
} from "@/config/constants";

export interface TraceEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

function eventBorderColor(type: string): string {
  if (type.includes("AGENT_SPAWNED")) return "border-l-indigo";
  if (type.includes("AGENT_COMPLETED")) return "border-l-mint";
  if (type.includes("AGENT_FAILED") || type.includes("STAGE_FAILED")) return "border-l-rose";
  if (type.includes("HYPOTHESIS_VALIDATED")) return "border-l-mint";
  if (type.includes("HYPOTHESIS_REJECTED")) return "border-l-rose";
  if (type.includes("HYPOTHESIS")) return "border-l-amber";
  if (type.includes("EXHAUSTED") || type.includes("BLOCKED")) return "border-l-rose";
  if (type.includes("EVIDENCE")) return "border-l-mint";
  if (type.includes("GROUNDING") || type.includes("RAG")) return "border-l-indigo";
  return "border-l-edge-subtle";
}

interface TraceEventRowProps {
  event: TraceEvent;
  expanded: boolean;
  onToggle: () => void;
}

export default function TraceEventRow({ event: ev, expanded, onToggle }: TraceEventRowProps) {
  const label = EVENT_LABELS[ev.event_type] || ev.event_type.replace(/_/g, " ");
  const p = (ev.payload || {}) as Record<string, string | number | boolean | null>;
  const phase = (p.phase as string) || "";
  const phaseColor = PHASE_COLORS[phase.toLowerCase()] || "text-ink-tertiary";
  const isError =
    ev.event_type.includes("FAILED") ||
    ev.event_type.includes("EXHAUSTED") ||
    ev.event_type.includes("REJECTED");

  return (
    <div
      className={`border-l-2 pl-4 py-2 cursor-pointer hover:bg-canvas-raised/50 transition-colors ${eventBorderColor(ev.event_type)}`}
      onClick={onToggle}
    >
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-2xs font-mono text-ink-tertiary w-16 shrink-0 tabular">
          {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ""}
        </span>
        <span
          className={`text-2xs font-medium ${isError ? "text-rose" : "text-ink-secondary"}`}
        >
          {label}
        </span>
        {phase && <span className={`text-2xs font-mono ${phaseColor}`}>{phase}</span>}
        {p.agent_type && (
          <span className="text-2xs font-mono text-indigo">
            {AGENT_TYPE_LABELS[p.agent_type as string] || p.agent_type}
          </span>
        )}
        {p.agent_id && (
          <span className="text-2xs font-mono text-ink-tertiary">
            {(p.agent_id as string).slice(0, 8)}
          </span>
        )}
        {p.hypothesis_id && (
          <span className="text-2xs font-mono text-amber">
            {(p.hypothesis_id as string).slice(0, 8)}
          </span>
        )}
        {p.confidence !== undefined && (
          <span className="text-2xs font-mono text-mint">
            {Math.round((p.confidence as number) * 100)}%
          </span>
        )}
        {p.opportunities !== undefined && (
          <span className="text-2xs font-mono text-mint">{p.opportunities} opps</span>
        )}
        {p.error && (
          <span className="text-2xs text-rose truncate max-w-xs">
            {String(p.error).slice(0, 60)}
          </span>
        )}
      </div>

      {expanded && (
        <div className="mt-2 ml-[76px] bg-canvas-raised border border-edge-subtle rounded-md p-3">
          <pre className="text-2xs text-ink-secondary font-mono whitespace-pre-wrap break-words leading-relaxed">
            {JSON.stringify(p, null, 2).slice(0, TRACE_JSON_TRUNCATE)}
          </pre>
        </div>
      )}
    </div>
  );
}
