"use client";

import { useState } from "react";
import type { TieredUseCase, Signal, MatchResult } from "@/lib/types";
import { ROI_LABELS, DATA_FLOW_LABELS, STRINGS } from "@/lib/config";
import ConfidenceBreakdownBar from "@/components/ConfidenceBreakdownBar";

interface UseCaseCardProps {
  useCase: TieredUseCase;
  signals?: Signal[];
  matchResults?: MatchResult[];
}

// Source badge display — maps raw source values to readable labels
const SOURCE_LABELS: Record<string, string> = {
  about_text: "About",
  job_posting: "Jobs",
  blog: "Blog",
  team_page: "Team",
  user_hint: "Your input",
};

function resolveMatchForUseCase(
  useCase: TieredUseCase,
  matchResults?: MatchResult[]
): MatchResult | undefined {
  if (!matchResults || matchResults.length === 0) return undefined;
  if (useCase.tier === "LOW_HANGING_FRUIT" && useCase.win_id) {
    return matchResults.find((m) => m.source_id === useCase.win_id);
  }
  if (useCase.tier === "MEDIUM_SOLUTION" && useCase.base_win_id) {
    return matchResults.find((m) => m.source_id === useCase.base_win_id);
  }
  return undefined;
}

export default function UseCaseCard({ useCase, signals, matchResults }: UseCaseCardProps) {
  const [dataFlowOpen, setDataFlowOpen] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const confidencePct = Math.round(useCase.confidence * 100);

  const supportingSignals = signals?.filter((s) =>
    useCase.evidence_signal_ids.includes(s.signal_id)
  ) ?? [];

  const relatedMatch = resolveMatchForUseCase(useCase, matchResults);
  const hasEvidence =
    supportingSignals.length > 0 ||
    relatedMatch !== undefined ||
    (useCase.tier === "HARD_EXPERIMENT" && !!useCase.rag_benchmark);

  const roiLabel = ROI_LABELS[useCase.tier] ?? "ROI";

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

      {/* Evidence collapsible — placeholder, filled in next step */}
      {hasEvidence && (
        <div className="pt-3 border-t" style={{ borderColor: "var(--rule)" }}>
          <button
            onClick={() => setEvidenceOpen(!evidenceOpen)}
            className="w-full flex items-center justify-between gap-2 text-left group"
            aria-expanded={evidenceOpen}
          >
            <span className="font-label text-xs uppercase tracking-[0.1em] text-ink-light group-hover:text-ink-medium transition-colors">
              Evidence
            </span>
            <span
              className="text-ink-light text-xs transition-transform duration-200"
              style={{ transform: evidenceOpen ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}
            >
              ▾
            </span>
          </button>
          {evidenceOpen && (
            <div className="mt-3 space-y-5">
              {supportingSignals.length > 0 && (
                <div>
                  <p className="font-label text-xs uppercase tracking-[0.1em] text-ink-light mb-2">
                    Supporting Signals
                  </p>
                  <div className="space-y-3">
                    {supportingSignals.map((sig) => (
                      <div key={sig.signal_id} className="pl-3 border-l" style={{ borderColor: "var(--rule)" }}>
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="font-label text-xs uppercase tracking-[0.06em] text-ink-medium">
                            {sig.type}
                          </span>
                          <span
                            className="font-mono text-xs px-1"
                            style={{ background: "var(--rule)", color: "var(--ink-light)" }}
                          >
                            {SOURCE_LABELS[sig.source] ?? sig.source}
                          </span>
                        </div>
                        <p className="font-body text-sm text-ink leading-relaxed">
                          {sig.value}
                        </p>
                        {sig.raw_quote && (
                          <p className="font-body text-xs italic text-ink-faint mt-0.5">
                            &ldquo;{sig.raw_quote}&rdquo;
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
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
            {STRINGS.dataFlow}
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
            {DATA_FLOW_LABELS.map(({ label, field }) => {
              const raw = useCase.data_flow[field as keyof typeof useCase.data_flow];
              const value = Array.isArray(raw) ? raw.join(", ") : String(raw ?? "");
              return { label, value };
            }).map(({ label, value }) => (
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
