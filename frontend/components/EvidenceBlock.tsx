import type { EvidenceItem } from "@/lib/types";

interface EvidenceBlockProps {
  evidence: EvidenceItem;
}

export default function EvidenceBlock({ evidence }: EvidenceBlockProps) {
  return (
    <div id={evidence.evidence_id} className="border border-border rounded-sm p-3 bg-surface">
      <div className="flex justify-between items-center mb-1">
        <span
          className="font-mono uppercase text-text-muted"
          style={{ fontSize: "11px", letterSpacing: "0.08em" }}
        >
          {evidence.source_type}
        </span>
        {evidence.uri && (
          <a
            href={evidence.uri}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-accent cursor-pointer"
            style={{ fontSize: "10px" }}
          >
            {evidence.uri.slice(0, 40)}
          </a>
        )}
      </div>
      <p className="text-text-primary mb-1" style={{ fontSize: "14px", fontWeight: 500 }}>
        {evidence.title}
      </p>
      <p
        className="font-mono text-text-muted italic mb-2"
        style={{
          fontSize: "13px",
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        &ldquo;{evidence.snippet}&rdquo;
      </p>
      <div className="flex gap-4">
        <span className="font-mono text-text-muted" style={{ fontSize: "12px" }}>
          relevance: {evidence.relevance_score.toFixed(2)}
        </span>
        {evidence.confidence_score != null && (
          <span className="font-mono text-text-muted" style={{ fontSize: "12px" }}>
            confidence: {evidence.confidence_score.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
}
