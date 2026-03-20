"use client";

import type { AnalyzeSuccess } from "@/lib/types";
import MatchResultCard from "@/components/MatchResultCard";
import TracePanel from "@/components/TracePanel";

interface EvidenceViewProps {
  data: AnalyzeSuccess;
}

function SignalTable({ data }: { data: AnalyzeSuccess }) {
  const signals = data.signals?.signals;
  if (!signals || signals.length === 0) return null;

  return (
    <div className="mb-8">
      <p className="font-label uppercase tracking-[0.1em] text-xs mb-3" style={{ color: "var(--ink-light)" }}>
        Extracted Signals
      </p>
      <div className="space-y-0">
        {signals.map((sig) => {
          const pct = Math.round(sig.confidence * 100);
          return (
            <div
              key={sig.signal_id}
              className="py-3 border-b"
              style={{ borderColor: "var(--rule)" }}
            >
              <div className="flex items-start justify-between gap-3 flex-wrap mb-1">
                <span className="font-label uppercase tracking-[0.06em] text-xs" style={{ color: "var(--ink-medium)" }}>
                  {sig.type}
                </span>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="font-mono text-xs" style={{ color: "var(--ink-light)" }}>
                    {sig.source}
                  </span>
                  <span className="font-mono text-xs font-bold" style={{ color: "var(--ink)" }}>
                    {pct}%
                  </span>
                </div>
              </div>
              <p className="font-body text-sm leading-relaxed" style={{ color: "var(--ink)" }}>
                {sig.value}
              </p>
              {sig.raw_quote && (
                <p className="font-mono text-xs mt-1 italic" style={{ color: "var(--ink-faint)" }}>
                  &ldquo;{sig.raw_quote}&rdquo;
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MatchResultsSection({ data }: { data: AnalyzeSuccess }) {
  const mr = data.match_results;
  if (!mr) return null;
  const all = [...(mr.delivered ?? []), ...(mr.adaptation ?? []), ...(mr.ambitious ?? [])];
  if (all.length === 0) return null;

  return (
    <div className="mb-8">
      <p className="font-label uppercase tracking-[0.1em] text-xs mb-3" style={{ color: "var(--ink-light)" }}>
        Victory Matches
        {data.has_user_hints && (
          <span className="ml-2 font-mono normal-case" style={{ color: "var(--ink-faint)" }}>
            enhanced with your context
          </span>
        )}
      </p>
      {all.map((r, i) => <MatchResultCard key={r.result_id ?? i} result={r} />)}
    </div>
  );
}

export default function EvidenceView({ data }: EvidenceViewProps) {
  return (
    <div className="py-4">
      <MatchResultsSection data={data} />
      <SignalTable data={data} />
      <TracePanel runId={data.run_id} />
    </div>
  );
}
