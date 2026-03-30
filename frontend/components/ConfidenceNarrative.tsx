function confidenceLabel(c: number): { text: string; color: string; barColor: string } {
  if (c >= 0.8) return { text: "Highly Confident", color: "text-mint", barColor: "bg-mint" };
  if (c >= 0.6) return { text: "Moderately Confident", color: "text-amber", barColor: "bg-amber" };
  return { text: "Low Confidence", color: "text-rose", barColor: "bg-rose" };
}

interface ConfidenceNarrativeProps {
  assessment: string;
  confidence: number;
}

export default function ConfidenceNarrative({ assessment, confidence }: ConfidenceNarrativeProps) {
  // Report-level: assessment text is the primary content, confidence bar supplements it
  if (assessment) {
    const { text, color, barColor } = confidenceLabel(confidence);
    return (
      <div className="bg-canvas-raised border border-edge-subtle rounded-md p-4 space-y-3">
        {confidence > 0 && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className={`text-xs font-semibold uppercase tracking-wider ${color}`}>
                {text}
              </span>
              <span className="text-xs text-ink-tertiary font-mono">
                {Math.round(confidence * 100)}%
              </span>
            </div>
            <div className="w-full h-1.5 bg-edge-subtle rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${barColor}`}
                style={{ width: `${Math.round(confidence * 100)}%` }}
              />
            </div>
          </div>
        )}
        <p className="text-sm text-ink-secondary leading-relaxed">{assessment}</p>
      </div>
    );
  }

  if (confidence === 0) return null;

  const { text, color, barColor } = confidenceLabel(confidence);
  const pct = Math.round(confidence * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className={`text-xs font-semibold uppercase tracking-wider ${color}`}>{text}</span>
        <span className="text-xs text-ink-tertiary font-mono">{pct}%</span>
      </div>
      <div className="w-full h-1.5 bg-edge-subtle rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
