"use client";

const DIMENSION_LABELS: { key: string; label: string }[] = [
  { key: "data_infrastructure", label: "Data Infrastructure" },
  { key: "ml_ai_capability", label: "ML / AI Capability" },
  { key: "strategy_intent", label: "Strategy & Intent" },
  { key: "operational_readiness", label: "Operational Readiness" },
];

interface MaturityBadgeProps {
  score?: number;
  label?: string;
  elapsedSeconds?: number;
  costUsd?: number;
  dimensions?: Record<string, number>;
}

function dimensionBarColor(val: number): string {
  if (val < 2) return "#c1272d";
  if (val <= 3.5) return "#1a1714";
  return "#2d6a4f";
}

function maturityTier(score: number): string {
  if (score < 1.5) return "Initial";
  if (score < 2.5) return "Developing";
  if (score < 3.5) return "Advancing";
  if (score < 4.5) return "Leading";
  return "Transformational";
}

export default function MaturityBadge({
  score,
  label,
  elapsedSeconds,
  costUsd,
  dimensions,
}: MaturityBadgeProps) {
  const displayLabel = label ?? (score !== undefined ? maturityTier(score) : "Complete");

  const metaParts: string[] = [];
  if (elapsedSeconds !== undefined) metaParts.push(`${elapsedSeconds.toFixed(1)}s`);
  if (costUsd !== undefined) metaParts.push(`$${costUsd.toFixed(4)}`);

  return (
    <div className="py-6">
      {/* Kicker */}
      <p className="font-label uppercase tracking-[0.12em] text-xs text-red mb-2">
        AI Maturity Score
      </p>

      {/* Score headline */}
      <div className="mb-1">
        <span className="font-headline text-6xl font-black text-ink leading-none">
          {score !== undefined ? score.toFixed(1) : "–"}
        </span>
      </div>
      <p className="font-body text-ink-light text-base mb-4">
        out of 5.0 — {displayLabel}
      </p>

      {/* Hairline separator */}
      <div className="rule-hairline mb-4" />

      {/* Dimension bars */}
      {dimensions && (
        <div className="space-y-3">
          <p className="font-label uppercase tracking-[0.1em] text-xs text-ink-light mb-2">
            Dimensions
          </p>
          {DIMENSION_LABELS.map(({ key, label: dimLabel }) => {
            const val = dimensions[key] ?? 0;
            const fill = dimensionBarColor(val);
            return (
              <div key={key}>
                <div className="flex justify-between items-baseline mb-1">
                  <span className="font-label text-xs text-ink-medium uppercase tracking-[0.06em]">
                    {dimLabel}
                  </span>
                  <span className="font-mono text-xs text-ink-light">{val.toFixed(1)}</span>
                </div>
                <div className="h-1.5 bg-rule overflow-hidden">
                  <div
                    className="h-1.5 transition-all duration-500"
                    style={{ width: `${(val / 5) * 100}%`, background: fill }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Metadata footer */}
      {metaParts.length > 0 && (
        <p className="font-mono text-xs text-ink-light mt-5">
          {metaParts.join(" | ")}
        </p>
      )}
    </div>
  );
}
