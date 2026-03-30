import type { EvidenceItem } from "@/lib/types";
import Badge from "@/components/ui/Badge";

const SOURCE_VARIANT: Record<string, "mint" | "indigo" | "amber" | "muted"> = {
  wins_kb: "indigo",
  google_search: "mint",
  user_provided: "amber",
};

export default function EvidenceCard({ evidence }: { evidence: EvidenceItem }) {
  const variant = SOURCE_VARIANT[evidence.source_type] ?? "muted";

  return (
    <div
      id={`ev-${evidence.evidence_id}`}
      className="bg-canvas-raised border border-edge-subtle rounded-md p-4"
    >
      <div className="flex items-center justify-between mb-2">
        <Badge variant={variant}>{evidence.source_type.replace(/_/g, " ")}</Badge>
        <span className="font-mono text-2xs text-ink-tertiary tabular">
          rel {evidence.relevance_score.toFixed(2)}
        </span>
      </div>

      <h4 className="text-base font-medium text-ink mb-1">{evidence.title}</h4>

      {evidence.uri && (
        <a
          href={evidence.uri}
          target="_blank"
          rel="noopener noreferrer"
          className="text-2xs text-mint hover:text-mint-bright transition-colors font-mono block mb-2 truncate"
        >
          {evidence.uri}
        </a>
      )}

      <div className="border-l-2 border-edge pl-3 mt-2">
        <p className="text-sm text-ink-secondary italic leading-relaxed max-w-prose">
          &ldquo;{evidence.snippet}&rdquo;
        </p>
      </div>

      {evidence.confidence_score != null && (
        <div className="mt-3 flex gap-4">
          <span className="font-mono text-2xs text-ink-tertiary">
            confidence {evidence.confidence_score.toFixed(2)}
          </span>
        </div>
      )}
    </div>
  );
}
