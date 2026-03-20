"use client";

import { useState, useImperativeHandle, forwardRef } from "react";
import type { UserHints } from "@/lib/types";

export const INDUSTRY_OPTIONS = [
  "logistics", "healthcare", "financial_services", "retail",
  "insurance", "professional_services", "manufacturing", "ecommerce",
  "fintech", "energy", "real_estate", "construction",
] as const;

export interface UserHintsPanelHandle {
  getHints: () => UserHints | null;
}

interface FieldsProps {
  inputBase: string;
  painPoints: string; setPainPoints: (v: string) => void;
  knownTech: string; setKnownTech: (v: string) => void;
  industry: string; setIndustry: (v: string) => void;
  employeeCount: string; setEmployeeCount: (v: string) => void;
  context: string; setContext: (v: string) => void;
}

// Filled in next commit
function HintsFields(_props: FieldsProps) { return null; }

const UserHintsPanel = forwardRef<UserHintsPanelHandle>((_, ref) => {
  const [expanded, setExpanded] = useState(false);
  const [painPoints, setPainPoints] = useState("");
  const [knownTech, setKnownTech] = useState("");
  const [industry, setIndustry] = useState("");
  const [employeeCount, setEmployeeCount] = useState("");
  const [context, setContext] = useState("");

  useImperativeHandle(ref, () => ({
    getHints(): UserHints | null {
      const hasAny = painPoints.trim() || knownTech.trim() || industry || employeeCount || context.trim();
      if (!hasAny) return null;
      return {
        pain_points: painPoints.trim() ? painPoints.split("\n").map((s) => s.trim()).filter(Boolean) : [],
        known_tech: knownTech.trim() ? knownTech.split(",").map((s) => s.trim()).filter(Boolean) : [],
        industry,
        employee_count: employeeCount ? parseInt(employeeCount, 10) : null,
        context: context.trim(),
      };
    },
  }));

  const inputBase = [
    "font-mono text-sm w-full",
    "border-0 border-b-[1.5px] border-ink bg-transparent",
    "focus:border-red outline-none py-2 px-0",
    "placeholder:text-ink-faint text-ink transition-colors",
  ].join(" ");

  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={() => setExpanded((p) => !p)}
        className="flex items-center gap-2 font-label uppercase tracking-[0.1em] text-xs text-ink-light hover:text-ink transition-colors"
        aria-expanded={expanded}
      >
        <span className="text-xs transition-transform duration-200 inline-block"
          style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}>
          &#9654;
        </span>
        Add Context (Optional)
      </button>
      {expanded && (
        <HintsFields inputBase={inputBase}
          painPoints={painPoints} setPainPoints={setPainPoints}
          knownTech={knownTech} setKnownTech={setKnownTech}
          industry={industry} setIndustry={setIndustry}
          employeeCount={employeeCount} setEmployeeCount={setEmployeeCount}
          context={context} setContext={setContext}
        />
      )}
    </div>
  );
});

UserHintsPanel.displayName = "UserHintsPanel";
export default UserHintsPanel;
