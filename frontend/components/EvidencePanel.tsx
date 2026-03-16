"use client";
import { useState } from "react";
import type { VictoryMatch } from "@/lib/types";

interface EvidencePanelProps {
  wins: VictoryMatch[];
}

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
            <div key={win.win_id ?? win.id} className="neo-flat p-3 text-xs space-y-1">
              <div className="flex items-center gap-2">
                <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-mono font-semibold">
                  {win.win_id ?? win.id}
                </span>
                <span className="font-medium text-gray-700">{win.engagement_title}</span>
              </div>
              <div className="flex gap-2 text-gray-400 flex-wrap">
                {win.industry && (
                  <span className="bg-gray-100 px-1.5 py-0.5 rounded">{win.industry}</span>
                )}
                {win.size_label && (
                  <span className="bg-gray-100 px-1.5 py-0.5 rounded">{win.size_label}</span>
                )}
                {win.maturity_at_engagement && (
                  <span className="bg-gray-100 px-1.5 py-0.5 rounded">{win.maturity_at_engagement}</span>
                )}
              </div>
              {win.primary_metric_value && (
                <p className="text-gray-600">
                  <span className="font-medium">{win.primary_metric_label}:</span>{" "}
                  {win.primary_metric_value}
                  {win.measurement_period && (
                    <span className="text-gray-400"> — {win.measurement_period}</span>
                  )}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
