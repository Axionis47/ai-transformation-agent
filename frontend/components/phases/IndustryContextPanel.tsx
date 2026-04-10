"use client";

import type { Run, IndustryContext } from "@/lib/types";

export default function IndustryContextPanel({ run }: { run: Run }) {
  const ic: IndustryContext | undefined = run.industry_context;
  if (!ic || !ic.industry) return null;
  const trends = ic.key_trends ?? [];
  return (
    <div className="mt-4 bg-canvas-raised border border-edge-subtle rounded-md p-5">
      <p className="text-xs text-indigo uppercase tracking-wider font-medium mb-3">
        Industry Context
      </p>
      <div className="space-y-2 text-sm text-ink-secondary">
        {ic.ai_adoption_level && (
          <p>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">AI ADOPTION</span>
            {ic.ai_adoption_level}
          </p>
        )}
        {ic.competitive_dynamics && (
          <p>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">COMPETITION</span>
            {ic.competitive_dynamics}
          </p>
        )}
        {trends.length > 0 && (
          <div>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">TRENDS</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {trends.slice(0, 5).map((t, i) => (
                <span
                  key={i}
                  className="bg-indigo/10 text-indigo text-2xs font-mono px-2 py-0.5 rounded"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
