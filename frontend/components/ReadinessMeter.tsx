"use client";

interface ReadinessMeterProps {
  score: number;
  label: string;
  nextAction: string;
}

function meterColor(score: number): string {
  if (score > 75) return "#2d6a4f";
  if (score >= 50) return "var(--ink-medium)";
  return "var(--red)";
}

export default function ReadinessMeter({
  score,
  label,
  nextAction,
}: ReadinessMeterProps) {
  const pct = Math.min(100, Math.max(0, score));
  const color = meterColor(pct);

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1">
        <span
          className="font-label uppercase tracking-[0.1em] text-xs"
          style={{ color: "var(--ink-light)" }}
        >
          Pitch Readiness
        </span>
        <div className="flex items-center gap-2">
          <span
            className="font-label uppercase tracking-[0.08em] text-xs"
            style={{ color }}
          >
            {label}
          </span>
          <span className="font-mono text-sm font-bold" style={{ color }}>
            {pct}%
          </span>
        </div>
      </div>
      <div className="h-1.5 w-full overflow-hidden" style={{ background: "var(--rule)" }}>
        <div
          className="h-1.5 transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      {nextAction && (
        <p className="font-body italic text-xs mt-1.5" style={{ color: "var(--ink-light)" }}>
          {nextAction}
        </p>
      )}
    </div>
  );
}
