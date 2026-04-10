"use client";

import { useState } from "react";
import FeedbackButton from "@/components/FeedbackButton";
import Badge from "@/components/ui/Badge";
import {
  TIER_BORDER,
  TIER_VARIANT,
  TIER_LABEL,
  TIER_TIMELINE,
} from "@/config/constants";
import type { ReportOpportunity, ReportFeedback } from "@/lib/types";

export default function OpportunityCard({
  opp,
  onFeedback,
  highlighted,
  isStartingPoint,
  defaultOpen,
}: {
  opp: ReportOpportunity;
  onFeedback: (fb: ReportFeedback) => void;
  highlighted?: boolean;
  isStartingPoint?: boolean;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const tier = opp.tier.toLowerCase();
  const pct = Math.round(opp.confidence * 100);
  const hasDetails =
    opp.conditions_for_success.length > 0 ||
    opp.risks.length > 0 ||
    opp.recommended_approach ||
    opp.evidence_summary;

  return (
    <div
      className={`group bg-canvas-raised border border-edge-subtle rounded-md border-l-[3px] ${TIER_BORDER[tier] ?? "border-l-edge"} print:break-inside-avoid print:bg-white print:border-gray-300 transition-all duration-500 ${highlighted ? "ring-1 ring-mint/40 bg-mint/5" : ""}`}
    >
      {/* Clickable header */}
      <div className="p-5 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-3 mb-2">
          {isStartingPoint && (
            <span className="inline-flex items-center gap-1 bg-mint/15 text-mint text-2xs font-semibold px-2 py-0.5 rounded-full">
              <span className="w-1 h-1 bg-mint rounded-full" />
              Start Here
            </span>
          )}
          <Badge variant={TIER_VARIANT[tier] ?? "muted"}>{TIER_LABEL[tier] ?? tier}</Badge>
          <span className="font-mono text-2xs text-ink-tertiary">{TIER_TIMELINE[tier]}</span>
          <div className="flex-1" />
          <span className="font-mono text-sm text-ink tabular">{pct}%</span>
          {hasDetails && (
            <span
              className={`text-ink-tertiary text-xs transition-transform ${open ? "rotate-90" : ""}`}
            >
              &#9654;
            </span>
          )}
        </div>
        <h3 className="text-base font-semibold text-ink print:text-black leading-snug">
          {opp.title}
        </h3>
        <p className="text-sm text-ink-secondary leading-relaxed mt-2 max-w-prose print:text-black">
          {opp.narrative}
        </p>
      </div>

      {/* Expandable detail sections */}
      <div
        className={`grid transition-all duration-300 ${open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}
      >
        <div className="overflow-hidden">
          <div className="px-5 pb-5 border-t border-edge-subtle pt-4 space-y-4">
            {opp.recommended_approach && (
              <div>
                <p className="text-2xs text-mint uppercase tracking-wider font-medium mb-2">
                  Implementation Plan
                </p>
                <p className="text-sm text-ink-secondary leading-relaxed print:text-black whitespace-pre-line">
                  {opp.recommended_approach}
                </p>
              </div>
            )}
            {opp.conditions_for_success.length > 0 && (
              <div>
                <p className="text-2xs text-amber uppercase tracking-wider font-medium mb-2">
                  Prerequisites
                </p>
                <ul className="space-y-1.5">
                  {opp.conditions_for_success.map((c, i) => (
                    <li key={i} className="text-sm text-ink-secondary flex items-start gap-2">
                      <span className="mt-1.5 w-1.5 h-1.5 bg-amber rounded-full shrink-0" />
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {opp.risks.length > 0 && (
              <div>
                <p className="text-2xs text-rose uppercase tracking-wider font-medium mb-2">
                  Risks
                </p>
                <ul className="space-y-1.5">
                  {opp.risks.map((r, i) => (
                    <li key={i} className="text-sm text-ink-secondary flex items-start gap-2">
                      <span className="mt-1.5 w-1.5 h-1.5 bg-rose rounded-full shrink-0" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {opp.evidence_summary && (
              <div>
                <p className="text-2xs text-indigo uppercase tracking-wider font-medium mb-2">
                  Supporting Evidence
                </p>
                <div className="border-l-2 border-indigo/20 pl-3">
                  <p className="text-sm text-ink-secondary leading-relaxed">
                    {opp.evidence_summary}
                  </p>
                  <a
                    href="#evidence-annex"
                    className="text-2xs text-indigo hover:underline font-mono mt-1.5 inline-block"
                  >
                    View full evidence ↓
                  </a>
                </div>
              </div>
            )}
            <div className="flex justify-end pt-1 print:hidden">
              <FeedbackButton
                targetSection={`opportunity:${opp.hypothesis_id}`}
                onSubmit={onFeedback}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Print: always show details */}
      <div className="hidden print:block px-5 pb-5 border-t border-gray-300 pt-4 space-y-3">
        {opp.recommended_approach && (
          <p className="text-sm text-black leading-relaxed">{opp.recommended_approach}</p>
        )}
        {opp.evidence_summary && (
          <p className="text-sm text-black leading-relaxed border-l-2 border-gray-300 pl-3">
            {opp.evidence_summary}
          </p>
        )}
      </div>
    </div>
  );
}
