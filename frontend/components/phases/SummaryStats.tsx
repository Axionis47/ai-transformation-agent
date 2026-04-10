"use client";

import type { Hypothesis } from "@/lib/types";
import Badge from "@/components/ui/Badge";

export default function SummaryStats({
  hypotheses,
  evidenceCount,
}: {
  hypotheses: Hypothesis[];
  evidenceCount: number;
}) {
  const validated = hypotheses.filter((h) => h.status === "validated").length;
  const rejected = hypotheses.filter((h) => h.status === "rejected").length;
  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      {[
        { label: "Validated", value: validated, variant: "mint" as const },
        { label: "Rejected", value: rejected, variant: "rose" as const },
        { label: "Evidence", value: evidenceCount, variant: "indigo" as const },
      ].map((s) => (
        <div
          key={s.label}
          className="bg-canvas-raised border border-edge-subtle rounded-md p-4 text-center"
        >
          <p className="text-2xl font-semibold font-mono text-ink">{s.value}</p>
          <p className="text-xs text-ink-tertiary uppercase tracking-wider mt-1">
            <Badge variant={s.variant}>{s.label}</Badge>
          </p>
        </div>
      ))}
    </div>
  );
}
