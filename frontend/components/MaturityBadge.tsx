"use client";

import {
  DIMENSION_LABELS,
  scoreColor,
  maturityTier,
  STRINGS,
} from "@/lib/config";

interface MaturityBadgeProps {
  score?: number;
  label?: string;
  elapsedSeconds?: number;
  costUsd?: number;
  dimensions?: Record<string, number>;
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
        {STRINGS.maturityScoreLabel}
      </p>

      {/* Score headline */}
      <div className="mb-1">
        <span className="font-headline text-6xl font-black text-ink leading-none">
          {score !== undefined ? score.toFixed(1) : "\u2013"}
        </span>
      </div>
      <p className="font-body text-ink-light text-base mb-4">
        out of 5.0 \u2014 {displayLabel}
      </p>

      {/* Hairline separator */}
      <div className="rule-hairline mb-4" />

      {/* Dimension bars */}
      {dimensions && (
        <div className="space-y-3">
          <p className="font-label uppercase tracking-[0.1em] text-xs text-ink-light mb-2">
            {STRINGS.dimensionsLabel}
          </p>
          {DIMENSION_LABELS.map(({ key, label: dimLabel }) => {
            const val = dimensions[key] ?? 0;
            const fill = scoreColor(val);
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
