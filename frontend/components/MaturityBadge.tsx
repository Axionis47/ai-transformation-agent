"use client";

interface MaturityBadgeProps {
  score?: number;
  label?: string;
  elapsedSeconds?: number;
  costUsd?: number;
}

function scoreColor(score: number): string {
  if (score < 2) return "text-red-600 bg-red-50";
  if (score < 3.5) return "text-yellow-700 bg-yellow-50";
  return "text-green-700 bg-green-50";
}

export default function MaturityBadge({
  score,
  label,
  elapsedSeconds,
  costUsd,
}: MaturityBadgeProps) {
  return (
    <div className="neo-raised p-6 flex flex-wrap items-center gap-6">
      {score !== undefined ? (
        <div className="flex flex-col items-center">
          <span className={`text-4xl font-bold px-4 py-2 rounded-neo-sm ${scoreColor(score)}`}>
            {score.toFixed(1)}
            <span className="text-lg font-normal text-gray-400">/5</span>
          </span>
          {label && (
            <span className="mt-2 text-sm font-medium text-gray-600">{label}</span>
          )}
          <span className="text-xs text-gray-400 mt-0.5">Maturity Score</span>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <span className="text-xl font-semibold text-green-700 bg-green-50 px-4 py-2 rounded-neo-sm">
            Analysis Complete
          </span>
        </div>
      )}

      <div className="flex gap-6 ml-auto text-sm text-gray-500">
        {elapsedSeconds !== undefined && (
          <div className="flex flex-col items-end">
            <span className="text-lg font-semibold text-gray-700">
              {elapsedSeconds.toFixed(1)}s
            </span>
            <span className="text-xs">elapsed</span>
          </div>
        )}
        {costUsd !== undefined && (
          <div className="flex flex-col items-end">
            <span className="text-lg font-semibold text-gray-700">
              ${costUsd.toFixed(4)}
            </span>
            <span className="text-xs">cost</span>
          </div>
        )}
      </div>
    </div>
  );
}
