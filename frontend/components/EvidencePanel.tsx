"use client";
import { useState } from "react";
import type { VictoryMatch } from "@/lib/types";

interface EvidencePanelProps {
  wins: VictoryMatch[];
}

const TIER_STYLES: Record<
  VictoryMatch["match_tier"],
  { label: string; bg: string; text: string; border: string }
> = {
  DIRECT_MATCH:      { label: "Direct",      bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
  CALIBRATION_MATCH: { label: "Calibration", bg: "#eff6ff", text: "#4f6df5", border: "#bfdbfe" },
  ADJACENT_MATCH:    { label: "Adjacent",    bg: "#fffbeb", text: "#d97706", border: "#fde68a" },
};

export default function EvidencePanel({ wins }: EvidencePanelProps) {
  const [open, setOpen] = useState(false);

  if (!wins || wins.length === 0) return null;

  return (
    <div className="mt-5 pt-4 border-t border-[#c4cad6]/40">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-2 group text-left"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 group-hover:text-gray-600 transition-colors">
            Supporting Evidence
          </span>
          <span
            className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
            style={{ background: "#e0e7ff", color: "#4f6df5" }}
          >
            {wins.length} {wins.length === 1 ? "source" : "sources"}
          </span>
        </div>
        <span
          className="text-gray-400 group-hover:text-gray-600 transition-all duration-200 text-sm"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div className="mt-3 space-y-3">
          {wins.map((win) => {
            const tier = TIER_STYLES[win.match_tier];
            return (
              <div key={win.win_id} className="neo-flat p-4 space-y-2">
                {/* Header row */}
                <div className="flex items-start gap-3 flex-wrap">
                  <span
                    className="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-gray-100 text-gray-500 shrink-0"
                  >
                    {win.win_id}
                  </span>
                  <span className="text-sm font-semibold flex-1 min-w-0" style={{ color: "#1e2433" }}>
                    {win.engagement_title}
                  </span>
                  <span
                    className="text-[11px] font-semibold px-2 py-0.5 rounded-full border shrink-0"
                    style={{ background: tier.bg, color: tier.text, borderColor: tier.border }}
                  >
                    {tier.label}
                  </span>
                </div>

                {/* Meta pills */}
                <div className="flex flex-wrap gap-2">
                  {win.industry && (
                    <span className="text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-500">
                      {win.industry}
                    </span>
                  )}
                  {win.similarity_score !== undefined && (
                    <span className="text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-500">
                      {(win.similarity_score * 100).toFixed(0)}% similar
                    </span>
                  )}
                  {win.confidence !== undefined && (
                    <span className="text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-500">
                      {(win.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                </div>

                {/* Notes */}
                {win.relevance_note && (
                  <p className="text-xs leading-relaxed" style={{ color: "#4a5568" }}>
                    {win.relevance_note}
                  </p>
                )}
                {win.roi_benchmark && (
                  <p className="text-xs font-semibold" style={{ color: "#4f6df5" }}>
                    ROI: {win.roi_benchmark}
                  </p>
                )}
                {win.gap_analysis && (
                  <p className="text-xs text-gray-400 italic">
                    Gap: {win.gap_analysis}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
