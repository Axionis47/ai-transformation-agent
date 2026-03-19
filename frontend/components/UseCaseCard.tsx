"use client";

import { useState } from "react";
import type { TieredUseCase } from "@/lib/types";

interface UseCaseCardProps {
  useCase: TieredUseCase;
}

export default function UseCaseCard({ useCase }: UseCaseCardProps) {
  const [dataFlowOpen, setDataFlowOpen] = useState(false);
  const confidencePct = Math.round(useCase.confidence * 100);

  const roiLabel =
    useCase.tier === "LOW_HANGING_FRUIT"
      ? "Proven ROI"
      : useCase.tier === "MEDIUM_SOLUTION"
      ? "Adapted ROI"
      : "Estimated ROI";

  return (
    <div className="py-6">
      {/* Title */}
      <h3 className="font-headline text-xl text-ink leading-snug mb-1">
        {useCase.title}
      </h3>

      {/* Effort / Impact */}
      <p className="font-label text-xs text-ink-light tracking-wide mb-4">
        {useCase.effort} effort&nbsp;&nbsp;|&nbsp;&nbsp;{useCase.impact} impact
      </p>

      {/* Description */}
      <p className="font-body text-ink leading-[1.75] mb-5">
        {useCase.description}
      </p>

      {/* ROI */}
      <div className="mb-4">
        <p className="font-label text-xs text-ink-light uppercase tracking-[0.1em] mb-1">
          {roiLabel}
        </p>
        <p className="font-mono font-bold text-ink text-base">{useCase.roi_estimate}</p>
        {useCase.roi_basis && (
          <p className="font-body text-sm text-ink-light mt-0.5">{useCase.roi_basis}</p>
        )}
      </div>

      {/* Confidence bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="font-label text-xs text-ink-light uppercase tracking-[0.1em]">
            Confidence
          </span>
          <span className="font-mono text-xs text-ink-light">{confidencePct}%</span>
        </div>
        <div className="h-1 w-full" style={{ background: "var(--rule)" }}>
          <div
            className="h-1 transition-all duration-500"
            style={{ width: `${confidencePct}%`, background: "var(--ink)" }}
          />
        </div>
      </div>

      {/* Why this company */}
      {useCase.why_this_company && (
        <p className="font-body italic text-ink-medium text-sm leading-relaxed mb-4">
          {useCase.why_this_company}
        </p>
      )}

      {/* LOW_HANGING_FRUIT evidence */}
      {useCase.tier === "LOW_HANGING_FRUIT" && (
        <div className="space-y-1.5 mb-4 font-body text-sm">
          {useCase.win_id && (
            <p className="text-ink-light">
              <span className="font-mono text-xs text-ink-medium">{useCase.win_id}</span>
              <span className="ml-2">proven engagement</span>
            </p>
          )}
          {useCase.proven_metric && (
            <p className="text-ink-medium">Proven: {useCase.proven_metric}</p>
          )}
          {useCase.client_profile_match && (
            <p className="text-ink-light">Similar: {useCase.client_profile_match}</p>
          )}
          {useCase.rag_benchmark && (
            <p className="text-ink-faint">Benchmark: {useCase.rag_benchmark}</p>
          )}
        </div>
      )}

      {/* MEDIUM_SOLUTION evidence */}
      {useCase.tier === "MEDIUM_SOLUTION" && (
        <div className="space-y-1.5 mb-4 font-body text-sm">
          {useCase.base_win_id && (
            <p className="text-ink-light">
              Based on <span className="font-mono text-xs text-ink-medium">{useCase.base_win_id}</span>
            </p>
          )}
          {useCase.adaptation_notes && (
            <div className="pl-3 border-l border-rule mt-2">
              <p className="font-label text-xs text-ink-light uppercase tracking-[0.1em] mb-1">
                Adaptation notes
              </p>
              <p className="font-body text-sm text-ink-medium leading-relaxed">
                {useCase.adaptation_notes}
              </p>
            </div>
          )}
          {useCase.adjusted_roi_range && (
            <p className="text-ink-light">Adjusted ROI: {useCase.adjusted_roi_range}</p>
          )}
          {useCase.rag_benchmark && (
            <p className="text-ink-faint">Benchmark: {useCase.rag_benchmark}</p>
          )}
        </div>
      )}

      {/* HARD_EXPERIMENT evidence */}
      {useCase.tier === "HARD_EXPERIMENT" && (
        <div className="space-y-2 mb-4 font-body text-sm">
          {useCase.industry_examples && useCase.industry_examples.length > 0 && (
            <div>
              <p className="font-label text-xs text-ink-light uppercase tracking-[0.1em] mb-1">
                Industry examples
              </p>
              <p className="text-ink-medium">{useCase.industry_examples.join(", ")}</p>
            </div>
          )}
          {useCase.source_citations && useCase.source_citations.length > 0 && (
            <div>
              <p className="font-label text-xs text-ink-light uppercase tracking-[0.1em] mb-1">
                Sources
              </p>
              <ul className="space-y-0.5">
                {useCase.source_citations.map((src) => (
                  <li key={src} className="text-ink-light font-mono text-xs">{src}</li>
                ))}
              </ul>
            </div>
          )}
          {useCase.rag_benchmark && (
            <p className="text-ink-faint">Industry ref: {useCase.rag_benchmark}</p>
          )}
        </div>
      )}

      {/* Data flow accordion */}
      <div className="pt-3 border-t" style={{ borderColor: "var(--rule)" }}>
        <button
          onClick={() => setDataFlowOpen(!dataFlowOpen)}
          className="w-full flex items-center justify-between gap-2 text-left group"
          aria-expanded={dataFlowOpen}
        >
          <span className="font-label text-xs uppercase tracking-[0.1em] text-ink-light group-hover:text-ink-medium transition-colors">
            Data Flow
          </span>
          <span
            className="text-ink-light text-xs transition-transform duration-200"
            style={{ transform: dataFlowOpen ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
          >
            ▾
          </span>
        </button>

        {dataFlowOpen && (
          <dl className="mt-3 space-y-2 pl-1">
            {[
              { label: "Inputs", value: useCase.data_flow.data_inputs.join(", ") },
              { label: "Model", value: useCase.data_flow.model_approach },
              { label: "Output", value: useCase.data_flow.output_consumer },
              { label: "Feedback", value: useCase.data_flow.feedback_loop },
              { label: "Measurement", value: useCase.data_flow.value_measurement },
            ].map(({ label, value }) => (
              <div key={label} className="flex gap-3 text-xs">
                <dt className="font-label uppercase tracking-[0.08em] text-ink-light min-w-[90px] shrink-0">
                  {label}
                </dt>
                <dd className="font-body text-ink-medium">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>

      {/* Hairline separator */}
      <div className="rule-hairline mt-6" />
    </div>
  );
}
