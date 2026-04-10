"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { useRun, useTrace } from "@/lib/hooks";
import Spinner from "@/components/ui/Spinner";
import TraceEventRow from "@/components/trace/TraceEvent";
import type { TraceEvent } from "@/components/trace/TraceEvent";
import TraceSidebar from "@/components/trace/TraceSidebar";
import TraceFilterBar from "@/components/trace/TraceFilterBar";
import type { Filter } from "@/components/trace/TraceFilterBar";

function matchesFilter(e: TraceEvent, f: Filter): boolean {
  if (f === "all") return true;
  if (f === "agents") return e.event_type.includes("AGENT") || e.event_type.includes("SPAWN");
  if (f === "hypotheses") return e.event_type.includes("HYPOTHESIS");
  if (f === "evidence")
    return (
      e.event_type.includes("GROUNDING") ||
      e.event_type.includes("RAG") ||
      e.event_type.includes("EVIDENCE")
    );
  if (f === "budget")
    return (
      e.event_type.includes("BUDGET") ||
      e.event_type.includes("EXHAUSTED") ||
      e.event_type.includes("QUERIES_COUNTED")
    );
  return true;
}

export default function TracePage() {
  const params = useParams();
  const runId = params.id as string;
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<Filter>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: run, error: runError } = useRun(runId);
  const { data: traceData, error: traceError } = useTrace(runId);

  const events = (traceData?.trace ?? []) as unknown as TraceEvent[];
  const agents = traceData?.agents ?? [];
  const error = runError || traceError;

  if (error)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-rose text-sm">{error instanceof Error ? error.message : "Failed to load trace"}</p>
      </div>
    );
  if (!run)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner size={24} />
      </div>
    );

  const searchUsed = run.budget_state.external_search_queries_used || 0;
  const searchTotal = run.budgets.external_search_query_budget;
  const ragUsed = run.budget_state.rag_queries_used || 0;
  const ragTotal = run.budgets.rag_query_budget;
  const filtered = events.filter((e) => matchesFilter(e, filter));

  return (
    <div className="min-h-screen bg-canvas">
      <header className="h-12 bg-canvas-raised border-b border-edge-subtle flex items-center px-6 shrink-0 sticky top-0 z-20">
        <Link
          href={`/run/${runId}`}
          className="text-2xs text-ink-tertiary hover:text-ink transition-colors font-mono"
        >
          &larr; Analysis
        </Link>
        <div className="w-px h-4 bg-edge mx-4" />
        <span className="text-2xs font-mono text-ink-tertiary uppercase tracking-[0.15em]">
          Trace
        </span>
        <div className="flex-1" />
        <Link
          href={`/run/${runId}/report`}
          className="text-2xs text-mint hover:text-mint-bright transition-colors font-mono"
        >
          Report &rarr;
        </Link>
      </header>

      <div className="flex">
        <TraceSidebar
          agents={agents}
          searchUsed={searchUsed}
          searchTotal={searchTotal}
          ragUsed={ragUsed}
          ragTotal={ragTotal}
        />

        <main className="flex-1 min-w-0 p-6">
          <div className="max-w-4xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-xl font-semibold text-ink">Event Trace</h1>
                <p className="text-sm text-ink-secondary mt-1">
                  {events.length} events · {run.company_intake?.company_name}
                </p>
              </div>
              <button
                onClick={() => {
                  queryClient.invalidateQueries({ queryKey: ["trace", runId] });
                  queryClient.invalidateQueries({ queryKey: ["run", runId] });
                }}
                className="text-2xs text-ink-tertiary hover:text-mint transition-colors font-mono"
              >
                Refresh
              </button>
            </div>

            <TraceFilterBar filter={filter} onFilterChange={setFilter} />

            <div className="space-y-1">
              {filtered.map((ev, i) => (
                <TraceEventRow
                  key={ev.event_id || i}
                  event={ev}
                  expanded={expandedId === ev.event_id}
                  onToggle={() => setExpandedId(expandedId === ev.event_id ? null : ev.event_id)}
                />
              ))}

              {filtered.length === 0 && (
                <p className="text-2xs text-ink-tertiary font-mono py-8 text-center">
                  No events for this filter.
                </p>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
