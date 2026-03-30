"use client";

import { useState } from "react";
import type { EvidenceItem } from "@/lib/types";
import Badge from "@/components/ui/Badge";
import ScoreBar from "@/components/ui/ScoreBar";

const SOURCE_BADGE: Record<string, { label: string; variant: "mint" | "indigo" | "muted" }> = {
  google_search: { label: "Google Search", variant: "mint" },
  wins_kb: { label: "Past Wins", variant: "indigo" },
  user_provided: { label: "User Provided", variant: "muted" },
};

const FILTERS = ["All", "Google Search", "Past Wins"] as const;
type Filter = (typeof FILTERS)[number];

const FILTER_SOURCE: Record<Filter, string | null> = {
  All: null,
  "Google Search": "google_search",
  "Past Wins": "wins_kb",
};

interface Props {
  evidence: EvidenceItem[];
  highlightId?: string;
}

export default function EvidenceAnnex({ evidence, highlightId }: Props) {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<Filter>("All");

  const filtered = FILTER_SOURCE[filter]
    ? evidence.filter((e) => e.source_type === FILTER_SOURCE[filter])
    : evidence;

  return (
    <section id="evidence-annex" className="mb-8">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-3 w-full text-left group"
      >
        <span
          className={`transition-transform text-[10px] text-ink-tertiary ${open ? "rotate-90" : ""}`}
        >
          &#9654;
        </span>
        <p className="text-xs text-ink-secondary uppercase tracking-wider font-medium">
          Evidence Annex ({evidence.length} items)
        </p>
        <div className="flex-1 border-t border-edge-subtle" />
      </button>

      {open && (
        <div className="mt-4 space-y-3">
          <div className="flex gap-2">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`text-2xs font-mono px-3 py-1 rounded transition-colors ${
                  filter === f
                    ? "bg-mint/15 text-mint"
                    : "text-ink-tertiary hover:text-ink-secondary"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {filtered.map((ev) => {
            const src = SOURCE_BADGE[ev.source_type] ?? {
              label: ev.source_type,
              variant: "muted" as const,
            };
            const isHighlighted = highlightId === ev.evidence_id;
            return (
              <div
                key={ev.evidence_id}
                id={ev.evidence_id}
                className={`bg-canvas-raised border rounded-md p-4 transition-colors ${
                  isHighlighted ? "bg-mint/10 border-mint/30" : "border-edge-subtle"
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="font-mono text-2xs text-ink-tertiary">
                    {ev.evidence_id.slice(0, 12)}
                  </span>
                  <Badge variant={src.variant}>{src.label}</Badge>
                  {ev.source_ref && (
                    <span className="text-2xs text-ink-tertiary truncate max-w-[200px]">
                      {ev.source_ref}
                    </span>
                  )}
                </div>
                <p className="text-sm font-semibold text-ink">{ev.title}</p>
                <p className="text-2xs text-ink-secondary line-clamp-2 mt-1 max-w-prose">
                  &ldquo;{ev.snippet}&rdquo;
                </p>
                <div className="mt-2 max-w-xs">
                  <ScoreBar value={ev.relevance_score} label="Relevance" color="mint" />
                </div>
                {(ev.dimension || ev.process_area) && (
                  <div className="flex gap-2 mt-2">
                    {ev.dimension && (
                      <span className="text-2xs font-mono text-ink-tertiary bg-canvas-overlay px-2 py-0.5 rounded">
                        {ev.dimension}
                      </span>
                    )}
                    {ev.process_area && (
                      <span className="text-2xs font-mono text-ink-tertiary bg-canvas-overlay px-2 py-0.5 rounded">
                        {ev.process_area}
                      </span>
                    )}
                  </div>
                )}
                {ev.uri && (
                  <a
                    href={ev.uri}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-2xs text-mint hover:underline font-mono mt-2 block truncate"
                  >
                    {ev.uri}
                  </a>
                )}
              </div>
            );
          })}

          {filtered.length === 0 && (
            <p className="text-2xs text-ink-tertiary font-mono py-4 text-center">
              No evidence for this filter.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
