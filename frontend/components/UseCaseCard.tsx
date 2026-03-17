"use client";

import { useState } from "react";
import type { TieredUseCase } from "@/lib/types";

const TIER_STYLES = {
  LOW_HANGING_FRUIT: {
    border: "border-l-[3px] border-green-500",
    badge: { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
    bar: "#16a34a",
    label: "Proven Solution",
  },
  MEDIUM_SOLUTION: {
    border: "border-l-[3px] border-amber-500",
    badge: { bg: "#fffbeb", text: "#d97706", border: "#fde68a" },
    bar: "#d97706",
    label: "Achievable Opportunity",
  },
  HARD_EXPERIMENT: {
    border: "border-l-[3px] border-blue-500",
    badge: { bg: "#eff6ff", text: "#4f6df5", border: "#bfdbfe" },
    bar: "#4f6df5",
    label: "Frontier Experiment",
  },
};

const EFFORT_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  Low:    { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
  Medium: { bg: "#fffbeb", text: "#d97706", border: "#fde68a" },
  High:   { bg: "#fef2f2", text: "#dc2626", border: "#fecaca" },
};

const IMPACT_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  Low:    { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
  Medium: { bg: "#eff6ff", text: "#4f6df5", border: "#bfdbfe" },
  High:   { bg: "#f5f3ff", text: "#7c3aed", border: "#ddd6fe" },
};

function Tag({ label, style }: { label: string; style: { bg: string; text: string; border: string } }) {
  return (
    <span
      className="text-[11px] font-semibold px-2 py-0.5 rounded-full border"
      style={{ background: style.bg, color: style.text, borderColor: style.border }}
    >
      {label}
    </span>
  );
}

interface UseCaseCardProps {
  useCase: TieredUseCase;
}

export default function UseCaseCard({ useCase }: UseCaseCardProps) {
  const [dataFlowOpen, setDataFlowOpen] = useState(false);
  const styles = TIER_STYLES[useCase.tier];
  const effortStyle = EFFORT_STYLES[useCase.effort] ?? EFFORT_STYLES.Medium;
  const impactStyle = IMPACT_STYLES[useCase.impact] ?? IMPACT_STYLES.Medium;
  const confidencePct = Math.round(useCase.confidence * 100);

  return (
    <div className={`neo-flat p-5 space-y-4 ${styles.border}`}>
      {/* Tags row */}
      <div className="flex flex-wrap items-center gap-2">
        <Tag label={styles.label} style={styles.badge} />
        <Tag label={`Effort: ${useCase.effort}`} style={effortStyle} />
        <Tag label={`Impact: ${useCase.impact}`} style={impactStyle} />
      </div>

      {/* Title */}
      <h3 className="text-sm font-bold leading-snug" style={{ color: "#1e2433" }}>
        {useCase.title}
      </h3>

      {/* Description */}
      <p className="text-sm leading-relaxed" style={{ color: "#4a5568" }}>
        {useCase.description}
      </p>

      {/* Confidence bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-gray-400">
            Confidence
          </span>
          <span className="text-xs font-bold" style={{ color: styles.bar }}>
            {confidencePct}%
          </span>
        </div>
        <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
          <div
            className="h-2 rounded-full transition-all duration-500"
            style={{ width: `${confidencePct}%`, background: styles.bar }}
          />
        </div>
      </div>

      {/* ROI estimate */}
      <div
        className="rounded-xl px-4 py-3 border"
        style={{ background: "#f8f9ff", borderColor: "#e0e7ff" }}
      >
        <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">
          ROI Estimate
        </p>
        <p className="text-sm font-semibold" style={{ color: "#4f6df5" }}>
          {useCase.roi_estimate}
        </p>
        {useCase.roi_basis && (
          <p className="text-xs text-gray-500 mt-0.5">{useCase.roi_basis}</p>
        )}
      </div>

      {/* Why this company */}
      {useCase.why_this_company && (
        <div className="rounded-xl px-4 py-3 bg-gray-50 border border-gray-200">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">
            Why this company
          </p>
          <p className="text-xs leading-relaxed" style={{ color: "#4a5568" }}>
            {useCase.why_this_company}
          </p>
        </div>
      )}

      {/* RAG benchmark */}
      {useCase.rag_benchmark && (
        <p className="text-[11px] text-gray-400">
          <span className="font-medium text-gray-500">Benchmark: </span>
          {useCase.rag_benchmark}
        </p>
      )}

      {/* Data flow accordion */}
      <div className="border-t border-[#c4cad6]/40 pt-3">
        <button
          onClick={() => setDataFlowOpen(!dataFlowOpen)}
          className="w-full flex items-center justify-between gap-2 text-left group"
          aria-expanded={dataFlowOpen}
        >
          <span className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 group-hover:text-gray-600 transition-colors">
            Data Flow
          </span>
          <span
            className="text-gray-400 group-hover:text-gray-600 transition-all duration-200"
            style={{ transform: dataFlowOpen ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
          >
            ▾
          </span>
        </button>

        {dataFlowOpen && (
          <div className="mt-3 space-y-2 pl-1">
            {[
              { label: "Inputs", value: useCase.data_flow.data_inputs.join(", ") },
              { label: "Model", value: useCase.data_flow.model_approach },
              { label: "Output", value: useCase.data_flow.output_consumer },
              { label: "Feedback", value: useCase.data_flow.feedback_loop },
              { label: "Measurement", value: useCase.data_flow.value_measurement },
            ].map(({ label, value }) => (
              <div key={label} className="flex gap-3 text-xs">
                <span className="font-semibold text-gray-500 min-w-[80px] shrink-0">{label}</span>
                <span style={{ color: "#4a5568" }}>{value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
