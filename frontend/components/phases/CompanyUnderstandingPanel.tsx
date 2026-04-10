"use client";

import type { Run, CompanyUnderstanding } from "@/lib/types";

export default function CompanyUnderstandingPanel({ run }: { run: Run }) {
  const cu: CompanyUnderstanding | undefined = run.company_understanding;
  if (!cu || !cu.what_they_do) return null;
  return (
    <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-5">
      <p className="text-xs text-indigo uppercase tracking-wider font-medium mb-3">
        Company Understanding
      </p>
      <div className="space-y-2 text-sm text-ink-secondary">
        {cu.what_they_do && (
          <p>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">DOES</span>
            {cu.what_they_do}
          </p>
        )}
        {cu.how_they_make_money && (
          <p>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">REVENUE</span>
            {cu.how_they_make_money}
          </p>
        )}
        {cu.size_and_scale && (
          <p>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">SCALE</span>
            {cu.size_and_scale}
          </p>
        )}
        {cu.technology_landscape && (
          <p>
            <span className="text-ink-tertiary font-mono text-2xs mr-2">TECH</span>
            {cu.technology_landscape}
          </p>
        )}
      </div>
    </div>
  );
}
