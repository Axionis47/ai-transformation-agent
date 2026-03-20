"use client";

import type { ConfidenceBreakdown } from "@/lib/types";

interface ConfidenceBreakdownBarProps {
  breakdown: ConfidenceBreakdown;
}

const CEILING_LABELS: Record<ConfidenceBreakdown["evidence_ceiling"], string> = {
  url_only: "Based on URL only",
  url_plus_hints: "Enhanced with your input",
  confirmed: "Confirmed",
};

const BAR_ROWS: { key: keyof ConfidenceBreakdown; label: string }[] = [
  { key: "industry_match", label: "Industry" },
  { key: "pain_point_match", label: "Pain Point" },
  { key: "tech_feasibility", label: "Tech" },
  { key: "scale_match", label: "Scale" },
  { key: "maturity_fit", label: "Maturity" },
  { key: "evidence_depth", label: "Evidence" },
];

export default function ConfidenceBreakdownBar({ breakdown }: ConfidenceBreakdownBarProps) {
  const ceilingLabel = CEILING_LABELS[breakdown.evidence_ceiling] ?? breakdown.evidence_ceiling;

  return (
    <div className="mt-3 space-y-1.5">
      {BAR_ROWS.map(({ key, label }) => {
        const raw = breakdown[key];
        const val = typeof raw === "number" ? raw : 0;
        const pct = Math.round(val * 100);
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="font-label text-xs text-ink-light w-20 shrink-0 uppercase tracking-[0.06em]">
              {label}
            </span>
            <div className="flex-1 h-1" style={{ background: "var(--rule)" }}>
              <div
                className="h-1 transition-all duration-500"
                style={{ width: `${pct}%`, background: "var(--ink)" }}
              />
            </div>
            <span className="font-mono text-xs text-ink-light w-9 text-right shrink-0">
              {pct}%
            </span>
          </div>
        );
      })}

      <div className="flex items-center gap-2 pt-1.5">
        <span
          className="font-label uppercase tracking-[0.06em] text-xs px-2 py-0.5"
          style={{ background: "var(--rule)", color: "var(--ink-medium)" }}
        >
          {ceilingLabel}
        </span>
      </div>

      {breakdown.explanation && (
        <p className="font-body italic text-xs text-ink-light leading-relaxed pt-0.5">
          {breakdown.explanation}
        </p>
      )}
    </div>
  );
}
