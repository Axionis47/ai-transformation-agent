"use client";

import type { MatchResult } from "@/lib/types";
import ConfidenceBreakdownBar from "@/components/ConfidenceBreakdownBar";

interface MatchResultCardProps {
  result: MatchResult;
}

const TIER_LABELS: Record<MatchResult["match_tier"], string> = {
  DELIVERED: "Delivered",
  ADAPTATION: "Adaptation",
  AMBITIOUS: "Ambitious",
};

const TIER_COLORS: Record<MatchResult["match_tier"], string> = {
  DELIVERED: "#2d6a4f",
  ADAPTATION: "#6b5b4f",
  AMBITIOUS: "#c1272d",
};

export default function MatchResultCard({ result }: MatchResultCardProps) {
  const pct = Math.round(result.confidence * 100);
  const tierColor = TIER_COLORS[result.match_tier];

  return (
    <div className="py-4 border-b" style={{ borderColor: "var(--rule)" }}>
      <div className="flex items-start justify-between gap-3 flex-wrap mb-1">
        <h4 className="font-headline text-base text-ink leading-snug flex-1">
          {result.source_title}
        </h4>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className="font-label uppercase tracking-[0.08em] text-xs px-2 py-0.5"
            style={{ color: tierColor, border: `1px solid ${tierColor}` }}
          >
            {TIER_LABELS[result.match_tier]}
          </span>
          <span className="font-mono text-sm font-bold" style={{ color: tierColor }}>
            {pct}%
          </span>
        </div>
      </div>

      {result.source_industry && (
        <p className="font-mono text-xs text-ink-light mb-2">{result.source_industry}</p>
      )}

      {result.relevance_note && (
        <p className="font-body text-sm text-ink-medium leading-relaxed mb-2">
          {result.relevance_note}
        </p>
      )}

      {result.proven_metrics && (
        <p className="font-mono text-xs text-ink-light mb-2">
          {result.proven_metrics.primary_label}: <span className="font-bold text-ink">{result.proven_metrics.primary_value}</span>
          {result.proven_metrics.measurement_period && (
            <span className="ml-1">({result.proven_metrics.measurement_period})</span>
          )}
        </p>
      )}

      {result.confidence_breakdown && (
        <ConfidenceBreakdownBar breakdown={result.confidence_breakdown} />
      )}
    </div>
  );
}
