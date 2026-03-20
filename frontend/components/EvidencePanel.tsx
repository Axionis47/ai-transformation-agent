"use client";
import { useState } from "react";
import type { VictoryMatch } from "@/lib/types";
import { EVIDENCE_TIER_LABELS, STRINGS } from "@/lib/config";

interface EvidencePanelProps {
  wins: VictoryMatch[];
}

export default function EvidencePanel({ wins }: EvidencePanelProps) {
  const [open, setOpen] = useState(false);

  if (!wins || wins.length === 0) return null;

  return (
    <div className="mt-5 pt-4" style={{ borderTop: "0.5px solid var(--rule)" }}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-2 group text-left"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <span className="font-label text-xs uppercase tracking-[0.12em] text-ink-light group-hover:text-ink-medium transition-colors">
            {STRINGS.supportingEvidence}
          </span>
          <span className="font-mono text-xs text-ink-faint">
            {wins.length} {wins.length === 1 ? "source" : "sources"}
          </span>
        </div>
        <span
          className="text-ink-light text-xs transition-transform duration-200"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div className="mt-4 space-y-0">
          {wins.map((win) => (
            <div key={win.win_id}>
              <div className="py-4 space-y-2">
                {/* Header row */}
                <div className="flex items-start gap-3 flex-wrap">
                  <span className="font-mono text-xs text-ink-medium shrink-0">
                    {win.win_id}
                  </span>
                  <span className="font-body font-bold text-sm text-ink flex-1 min-w-0">
                    {win.engagement_title}
                  </span>
                  <span className="font-label text-xs text-ink-light shrink-0">
                    {EVIDENCE_TIER_LABELS[win.match_tier]}
                  </span>
                </div>

                {/* Meta */}
                <div className="flex flex-wrap gap-4 font-label text-xs text-ink-faint">
                  {win.industry && <span>{win.industry}</span>}
                  {win.similarity_score !== undefined && (
                    <span>{(win.similarity_score * 100).toFixed(0)}% similar</span>
                  )}
                  {win.confidence !== undefined && (
                    <span>{(win.confidence * 100).toFixed(0)}% confidence</span>
                  )}
                </div>

                {/* Notes */}
                {win.relevance_note && (
                  <p className="font-body text-sm text-ink-medium leading-relaxed">
                    {win.relevance_note}
                  </p>
                )}
                {win.roi_benchmark && (
                  <p className="font-mono font-bold text-sm text-ink">
                    ROI: {win.roi_benchmark}
                  </p>
                )}
                {win.gap_analysis && (
                  <p className="font-body text-sm text-ink-light italic">
                    Gap: {win.gap_analysis}
                  </p>
                )}
              </div>
              <div style={{ borderTop: "0.5px solid var(--rule)" }} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
