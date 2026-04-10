"use client";

import type { Run, PainPoint } from "@/lib/types";

export default function PainPointsPanel({ run }: { run: Run }) {
  const pps: PainPoint[] | undefined = run.pain_points;
  if (!pps || pps.length === 0) return null;
  return (
    <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-5">
      <p className="text-xs text-amber uppercase tracking-wider font-medium mb-3">
        Discovered Pain Points ({pps.length})
      </p>
      <div className="space-y-3">
        {pps.map((pp, i) => (
          <div key={i} className="flex items-start gap-2">
            <span
              className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                pp.severity === "high"
                  ? "bg-rose"
                  : pp.severity === "medium"
                    ? "bg-amber"
                    : "bg-mint"
              }`}
            />
            <div>
              <p className="text-sm text-ink">{pp.description}</p>
              <p className="text-2xs text-ink-tertiary font-mono mt-0.5">
                {pp.affected_process}
                {pp.severity && <> &middot; {pp.severity.toUpperCase()}</>}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
