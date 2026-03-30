"use client";

interface PhaseProgressProps {
  currentPhase: string;
  phases: string[];
}

const LABELS: Record<string, string> = {
  INTAKE: "Intake",
  GROUNDING: "Ground",
  DEEP_RESEARCH: "Research",
  HYPOTHESIS_FORMATION: "Hypothesize",
  HYPOTHESIS_TESTING: "Test",
  SYNTHESIS: "Synthesize",
  REVIEW: "Review",
};

export default function PhaseProgress({ currentPhase, phases }: PhaseProgressProps) {
  const currentIdx = phases.indexOf(currentPhase);

  return (
    <div className="flex items-center gap-0 overflow-x-auto py-2">
      {phases.map((phase, idx) => {
        const isCurrent = idx === currentIdx;
        const isComplete = idx < currentIdx;
        const isFuture = idx > currentIdx;

        return (
          <div key={phase} className="flex items-center">
            {idx > 0 && (
              <div
                className={`w-8 h-px shrink-0 ${isComplete ? "bg-mint" : isCurrent ? "bg-mint/50" : "bg-edge-subtle"}`}
              />
            )}
            <div className="flex flex-col items-center gap-1.5 shrink-0">
              <div
                className={`relative w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
                  isComplete
                    ? "bg-mint border-mint"
                    : isCurrent
                      ? "border-mint bg-transparent"
                      : "border-edge-subtle bg-transparent"
                }`}
              >
                {isComplete && (
                  <svg
                    className="w-2.5 h-2.5 text-canvas"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {isCurrent && (
                  <span className="absolute inset-0 rounded-full bg-mint/30 animate-pulse" />
                )}
              </div>
              <span
                className={`text-center font-mono leading-none whitespace-nowrap ${
                  isCurrent
                    ? "text-mint font-semibold"
                    : isComplete
                      ? "text-ink-secondary"
                      : "text-ink-tertiary"
                }`}
                style={{ fontSize: "9px", letterSpacing: "0.04em" }}
              >
                {LABELS[phase] ?? phase}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
