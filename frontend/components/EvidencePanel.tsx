"use client";
import { useState } from "react";
import type { VictoryMatch } from "@/lib/types";

interface EvidencePanelProps {
  wins: VictoryMatch[];
}

const TIER_LABELS: Record<VictoryMatch["match_tier"], string> = {
  DIRECT_MATCH: "Direct",
  CALIBRATION_MATCH: "Calibration",
  ADJACENT_MATCH: "Adjacent",
};

const TIER_COLORS: Record<VictoryMatch["match_tier"], string> = {
  DIRECT_MATCH: "bg-green-100 text-green-700",
  CALIBRATION_MATCH: "bg-blue-100 text-blue-700",
  ADJACENT_MATCH: "bg-yellow-100 text-yellow-700",
};

export default function EvidencePanel({ wins }: EvidencePanelProps) {
  const [open, setOpen] = useState(false);

  if (!wins || wins.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs font-medium text-gray-500 hover:text-gray-700 flex items-center gap-1"
      >
        {open ? "▾" : "▸"} Show Sources ({wins.length} wins)
      </button>
      {open && (
        <div className="mt-2 space-y-2">
          {wins.map((win) => (
            <div key={win.win_id} className="neo-flat p-3 text-xs space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono font-semibold">
                  {win.win_id}
                </span>
                <span className="font-medium text-gray-700">{win.engagement_title}</span>
                <span className={`ml-auto px-2 py-0.5 rounded font-semibold ${TIER_COLORS[win.match_tier]}`}>
                  {TIER_LABELS[win.match_tier]}
                </span>
              </div>
              <div className="flex gap-2 text-gray-400 flex-wrap">
                {win.industry && (
                  <span className="bg-gray-100 px-1.5 py-0.5 rounded">{win.industry}</span>
                )}
                {win.similarity_score !== undefined && (
                  <span className="bg-gray-100 px-1.5 py-0.5 rounded">
                    {(win.similarity_score * 100).toFixed(0)}% similar
                  </span>
                )}
                {win.confidence !== undefined && (
                  <span className="bg-gray-100 px-1.5 py-0.5 rounded">
                    {(win.confidence * 100).toFixed(0)}% confidence
                  </span>
                )}
              </div>
              {win.relevance_note && (
                <p className="text-gray-600">{win.relevance_note}</p>
              )}
              {win.roi_benchmark && (
                <p className="text-gray-700 font-medium">ROI: {win.roi_benchmark}</p>
              )}
              {win.gap_analysis && (
                <p className="text-gray-500 italic">Gap: {win.gap_analysis}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
