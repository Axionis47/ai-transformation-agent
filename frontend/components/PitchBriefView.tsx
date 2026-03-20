"use client";

import type { AnalyzeSuccess } from "@/lib/types";

interface PitchBriefViewProps {
  data: AnalyzeSuccess;
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-label uppercase tracking-[0.12em] text-xs mb-2" style={{ color: "var(--red)" }}>
      {children}
    </p>
  );
}

export default function PitchBriefView({ data }: PitchBriefViewProps) {
  const brief = data.pitch_brief;

  if (!brief) {
    return (
      <div className="py-12 text-center">
        <p className="font-body text-sm" style={{ color: "var(--ink-light)" }}>
          Run analysis to generate pitch brief
        </p>
      </div>
    );
  }

  const objectionPairs = brief.objection_prep
    .split(/\n+/)
    .filter(Boolean)
    .map((line) => {
      const sep = line.indexOf("→");
      if (sep === -1) return { objection: line, response: "" };
      return { objection: line.slice(0, sep).trim(), response: line.slice(sep + 1).trim() };
    });

  return (
    <div className="space-y-8 py-4">
      <div>
        <SectionHeading>Opening Line</SectionHeading>
        <blockquote
          className="font-headline text-xl leading-snug pl-4 border-l-2"
          style={{ borderColor: "var(--red)", color: "var(--ink)" }}
        >
          {brief.opening_line}
        </blockquote>
      </div>

      <div>
        <SectionHeading>The Story</SectionHeading>
        <p className="font-body leading-[1.75] pl-4" style={{ color: "var(--ink-medium)" }}>
          {brief.story}
        </p>
      </div>

      <div>
        <SectionHeading>ROI Conversation</SectionHeading>
        <p className="font-body leading-[1.75]" style={{ color: "var(--ink)" }}>
          {brief.roi_conversation}
        </p>
      </div>

      <div>
        <SectionHeading>Questions to Ask</SectionHeading>
        <ol className="space-y-4">
          {brief.questions.map((q, i) => (
            <li key={i} className="flex gap-3">
              <span className="font-mono text-xs mt-0.5 shrink-0" style={{ color: "var(--ink-light)" }}>
                {String(i + 1).padStart(2, "0")}
              </span>
              <p className="font-body text-sm leading-relaxed" style={{ color: "var(--ink)" }}>
                {q}
              </p>
            </li>
          ))}
        </ol>
      </div>

      <div>
        <SectionHeading>Objection Prep</SectionHeading>
        <div className="space-y-3">
          {objectionPairs.map((pair, i) => (
            <div key={i} className="pl-3 border-l" style={{ borderColor: "var(--rule)" }}>
              <p className="font-label text-xs uppercase tracking-[0.08em] mb-0.5" style={{ color: "var(--ink-light)" }}>
                Objection
              </p>
              <p className="font-body text-sm mb-1" style={{ color: "var(--ink)" }}>{pair.objection}</p>
              {pair.response && (
                <>
                  <p className="font-label text-xs uppercase tracking-[0.08em] mb-0.5" style={{ color: "var(--red)" }}>
                    Response
                  </p>
                  <p className="font-body text-sm" style={{ color: "var(--ink-medium)" }}>{pair.response}</p>
                </>
              )}
            </div>
          ))}
        </div>
      </div>

      {brief.honest_conversation && (
        <div>
          <SectionHeading>From a Similar Engagement</SectionHeading>
          <p className="font-body leading-[1.75] pl-4" style={{ color: "var(--ink-medium)" }}>
            {brief.honest_conversation}
          </p>
        </div>
      )}
    </div>
  );
}
