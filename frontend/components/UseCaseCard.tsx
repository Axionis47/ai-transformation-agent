"use client";

import { useState } from "react";
import type { TieredUseCase } from "@/lib/types";

const TIER_STYLES = {
  LOW_HANGING_FRUIT: {
    border: "border-l-4 border-green-500",
    badge: "bg-green-100 text-green-700",
    bar: "bg-green-500",
    label: "Proven Solution",
  },
  MEDIUM_SOLUTION: {
    border: "border-l-4 border-amber-500",
    badge: "bg-amber-100 text-amber-700",
    bar: "bg-amber-500",
    label: "Achievable Opportunity",
  },
  HARD_EXPERIMENT: {
    border: "border-l-4 border-blue-500",
    badge: "bg-blue-100 text-blue-700",
    bar: "bg-blue-500",
    label: "Frontier Experiment",
  },
};

const EFFORT_COLORS: Record<string, string> = {
  Low: "bg-green-100 text-green-700",
  Medium: "bg-amber-100 text-amber-700",
  High: "bg-red-100 text-red-700",
};

interface UseCaseCardProps {
  useCase: TieredUseCase;
}

export default function UseCaseCard({ useCase }: UseCaseCardProps) {
  const [dataFlowOpen, setDataFlowOpen] = useState(false);
  const styles = TIER_STYLES[useCase.tier];

  return (
    <div className={`neo-flat p-5 space-y-3 ${styles.border}`}>
      <div className="flex flex-wrap items-start gap-2">
        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${styles.badge}`}>
          {styles.label}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded ${EFFORT_COLORS[useCase.effort]}`}>
          Effort: {useCase.effort}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded ${EFFORT_COLORS[useCase.impact]}`}>
          Impact: {useCase.impact}
        </span>
      </div>
      <h3 className="text-sm font-semibold text-gray-800">{useCase.title}</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{useCase.description}</p>
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Confidence</span>
          <span>{Math.round(useCase.confidence * 100)}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-gray-200">
          <div className={`h-1.5 rounded-full ${styles.bar}`} style={{ width: `${useCase.confidence * 100}%` }} />
        </div>
      </div>
      <div className="text-xs text-gray-600 space-y-0.5">
        <span className="font-medium text-gray-700">ROI: </span>{useCase.roi_estimate}
        {useCase.roi_basis && <span className="text-gray-400"> — {useCase.roi_basis}</span>}
      </div>
      {useCase.why_this_company && (
        <div className="text-xs bg-gray-50 rounded p-2 text-gray-600">
          <span className="font-medium text-gray-700">Why you: </span>{useCase.why_this_company}
        </div>
      )}
      {useCase.rag_benchmark && (
        <div className="text-xs text-gray-400">Benchmark: {useCase.rag_benchmark}</div>
      )}
      <button
        onClick={() => setDataFlowOpen(!dataFlowOpen)}
        className="text-xs font-medium text-gray-500 hover:text-gray-700 flex items-center gap-1"
      >
        {dataFlowOpen ? "▾" : "▸"} Data Flow
      </button>
      {dataFlowOpen && (
        <div className="text-xs text-gray-600 space-y-1 pl-3 border-l border-gray-200">
          <p><span className="font-medium">Inputs:</span> {useCase.data_flow.data_inputs.join(", ")}</p>
          <p><span className="font-medium">Model:</span> {useCase.data_flow.model_approach}</p>
          <p><span className="font-medium">Output:</span> {useCase.data_flow.output_consumer}</p>
          <p><span className="font-medium">Feedback:</span> {useCase.data_flow.feedback_loop}</p>
          <p><span className="font-medium">Measurement:</span> {useCase.data_flow.value_measurement}</p>
        </div>
      )}
    </div>
  );
}
