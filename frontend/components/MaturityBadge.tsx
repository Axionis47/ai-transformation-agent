"use client";

interface DimensionScores {
  data_infrastructure?: number;
  ml_ai_capability?: number;
  strategy_intent?: number;
  operational_readiness?: number;
}

interface MaturityBadgeProps {
  score?: number;
  label?: string;
  elapsedSeconds?: number;
  costUsd?: number;
  dimensions?: DimensionScores;
}

const DIMENSION_LABELS: { key: keyof DimensionScores; label: string }[] = [
  { key: "data_infrastructure", label: "Data Infra" },
  { key: "ml_ai_capability", label: "ML/AI" },
  { key: "strategy_intent", label: "Strategy" },
  { key: "operational_readiness", label: "Ops Ready" },
];

function scoreColor(score: number): string {
  if (score < 2) return "text-red-600 bg-red-50";
  if (score < 3.5) return "text-yellow-700 bg-yellow-50";
  return "text-green-700 bg-green-50";
}

function barColor(val: number): string {
  if (val < 2) return "bg-red-400";
  if (val < 3.5) return "bg-yellow-400";
  return "bg-green-400";
}

export default function MaturityBadge({
  score,
  label,
  elapsedSeconds,
  costUsd,
  dimensions,
}: MaturityBadgeProps) {
  return (
    <div className="neo-raised p-5 space-y-4">
      <div className="flex flex-wrap items-center gap-6">
        {score !== undefined ? (
          <div className="flex flex-col items-center">
            <span className={`text-3xl font-bold px-3 py-1.5 rounded-neo-sm ${scoreColor(score)}`}>
              {score.toFixed(1)}
              <span className="text-base font-normal text-gray-400">/5</span>
            </span>
            {label && (
              <span className="mt-1.5 text-sm font-medium text-gray-700">{label}</span>
            )}
            <span className="text-xs text-gray-400 mt-0.5">Maturity Score</span>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <span className="text-lg font-semibold text-green-700 bg-green-50 px-3 py-1.5 rounded-neo-sm">
              Analysis Complete
            </span>
          </div>
        )}
        <div className="flex gap-6 ml-auto text-sm text-gray-500">
          {elapsedSeconds !== undefined && (
            <div className="flex flex-col items-end">
              <span className="text-base font-semibold text-gray-700">{elapsedSeconds.toFixed(1)}s</span>
              <span className="text-xs">elapsed</span>
            </div>
          )}
          {costUsd !== undefined && (
            <div className="flex flex-col items-end">
              <span className="text-base font-semibold text-gray-700">${costUsd.toFixed(4)}</span>
              <span className="text-xs">cost</span>
            </div>
          )}
        </div>
      </div>
      {dimensions && (
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          {DIMENSION_LABELS.map(({ key, label: dimLabel }) => {
            const val = dimensions[key] ?? 0;
            return (
              <div key={key} className="space-y-0.5">
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{dimLabel}</span>
                  <span>{val.toFixed(1)}/5</span>
                </div>
                <div className="h-1.5 rounded-full bg-gray-200">
                  <div
                    className={`h-1.5 rounded-full ${barColor(val)}`}
                    style={{ width: `${(val / 5) * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
