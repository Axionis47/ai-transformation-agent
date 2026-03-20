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

function HintsFields({
  inputBase, painPoints, setPainPoints, knownTech, setKnownTech,
  industry, setIndustry, employeeCount, setEmployeeCount, context, setContext,
}: FieldsProps) {
  return (
    <div className="mt-4 space-y-5 pl-4 border-l-2" style={{ borderColor: "var(--rule)" }}>
      <div>
        <label className="font-label uppercase tracking-[0.08em] text-xs text-ink-light block mb-1">
          Pain Points <span className="font-mono normal-case text-ink-faint ml-1">one per line</span>
        </label>
        <textarea rows={3} value={painPoints} onChange={(e) => setPainPoints(e.target.value)}
          placeholder={"manual invoice processing takes 40 hours/week\ncustomer churn is high in Q1"}
          className={inputBase + " resize-none"} />
      </div>
      <div>
        <label className="font-label uppercase tracking-[0.08em] text-xs text-ink-light block mb-1">
          Known Tech Stack <span className="font-mono normal-case text-ink-faint ml-1">comma-separated</span>
        </label>
        <input type="text" value={knownTech} onChange={(e) => setKnownTech(e.target.value)}
          placeholder="SAP, AWS, Salesforce" className={inputBase} />
      </div>
      <div className="flex gap-6 flex-col sm:flex-row">
        <div className="flex-1">
          <label className="font-label uppercase tracking-[0.08em] text-xs text-ink-light block mb-1">
            Industry
          </label>
          <select value={industry} onChange={(e) => setIndustry(e.target.value)}
            className={inputBase + " cursor-pointer"}>
            <option value="">Select industry...</option>
            {INDUSTRY_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="font-label uppercase tracking-[0.08em] text-xs text-ink-light block mb-1">
            Employee Count
          </label>
          <input type="number" min={1} value={employeeCount}
            onChange={(e) => setEmployeeCount(e.target.value)}
            placeholder="200" className={inputBase} />
        </div>
      </div>
      <div>
        <label className="font-label uppercase tracking-[0.08em] text-xs text-ink-light block mb-1">
          Additional Context <span className="font-mono normal-case text-ink-faint ml-1">max 1000 chars</span>
        </label>
        <textarea rows={3} maxLength={1000} value={context} onChange={(e) => setContext(e.target.value)}
          placeholder="Tried a chatbot last year, abandoned it."
          className={inputBase + " resize-none"} />
        {context.length > 800 && (
          <p className="font-mono text-xs text-ink-light mt-1 text-right">{context.length}/1000</p>
        )}
      </div>
    </div>
  );
}

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
