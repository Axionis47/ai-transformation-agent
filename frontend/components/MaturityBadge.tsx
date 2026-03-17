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

function scoreAccent(score: number): { ring: string; fill: string; text: string } {
  if (score < 2) return { ring: "#ef4444", fill: "#ef4444", text: "#dc2626" };
  if (score < 3.5) return { ring: "#f59e0b", fill: "#f59e0b", text: "#d97706" };
  return { ring: "#4f6df5", fill: "#4f6df5", text: "#4f6df5" };
}

function barFill(val: number): string {
  if (val < 2) return "#ef4444";
  if (val < 3.5) return "#f59e0b";
  return "#4f6df5";
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
  const accent = score !== undefined ? scoreAccent(score) : scoreAccent(3.5);
  const displayLabel = label ?? (score !== undefined ? maturityTier(score) : "Complete");

  return (
    <div className="neo-raised p-6 space-y-5">
      {/* Top row: score + metadata */}
      <div className="flex flex-wrap items-start gap-6">
        {/* Score block */}
        <div className="flex items-center gap-5">
          {/* Large circular score */}
          <div
            className="relative flex items-center justify-center w-20 h-20 rounded-full"
            style={{
              background: `conic-gradient(${accent.fill} 0% ${score !== undefined ? (score / 5) * 100 : 100}%, #d1d5db ${score !== undefined ? (score / 5) * 100 : 100}% 100%)`,
              padding: "3px",
            }}
          >
            <div className="w-full h-full rounded-full bg-[#edf0f5] flex flex-col items-center justify-center">
              <span className="text-2xl font-extrabold leading-none" style={{ color: accent.text }}>
                {score !== undefined ? score.toFixed(1) : "–"}
              </span>
              <span className="text-[10px] font-medium text-gray-400 leading-none mt-0.5">/5</span>
            </div>
          </div>
          {/* Label block */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">
              AI Maturity Score
            </span>
            <span
              className="text-xl font-bold leading-tight"
              style={{ color: "#1e2433" }}
            >
              {displayLabel}
            </span>
            <span
              className="inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full"
              style={{
                background: accent.fill + "18",
                color: accent.text,
                border: `1px solid ${accent.fill}40`,
              }}
            >
              {score !== undefined ? `${Math.round((score / 5) * 100)}th percentile` : "Analysis complete"}
            </span>
          </div>
        </div>

        {/* Metadata: elapsed + cost */}
        <div className="ml-auto flex gap-4 self-center">
          {elapsedSeconds !== undefined && (
            <div className="neo-flat px-4 py-2.5 flex flex-col items-center min-w-[72px]">
              <span className="text-base font-bold text-gray-700 leading-none">
                {elapsedSeconds.toFixed(1)}s
              </span>
              <span className="text-[10px] text-gray-400 mt-1 uppercase tracking-widest">Runtime</span>
            </div>
          )}
          {costUsd !== undefined && (
            <div className="neo-flat px-4 py-2.5 flex flex-col items-center min-w-[72px]">
              <span className="text-base font-bold text-gray-700 leading-none">
                ${costUsd.toFixed(4)}
              </span>
              <span className="text-[10px] text-gray-400 mt-1 uppercase tracking-widest">Cost</span>
            </div>
          )}
        </div>
      </div>

      {/* Dimension bars */}
      {dimensions && (
        <div className="pt-4 border-t border-[#c4cad6]/40">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-3">
            Dimension Breakdown
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
            {DIMENSION_LABELS.map(({ key, label: dimLabel }) => {
              const val = dimensions[key] ?? 0;
              const fill = barFill(val);
              return (
                <div key={key} className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-medium text-gray-600">{dimLabel}</span>
                    <span className="text-xs font-bold" style={{ color: fill }}>
                      {val.toFixed(1)}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
                    <div
                      className="h-2 rounded-full transition-all duration-500"
                      style={{ width: `${(val / 5) * 100}%`, background: fill }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
