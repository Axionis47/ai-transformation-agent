"use client";

import type { TieredUseCase } from "@/lib/types";
import UseCaseCard from "@/components/UseCaseCard";

interface UseCaseTierSectionProps {
  useCases: TieredUseCase[];
  id?: string;
}

const TIER_SECTIONS = [
  {
    tier: "LOW_HANGING_FRUIT" as const,
    heading: "PROVEN SOLUTIONS",
    subtitle: "Validated approaches with direct evidence",
    accentColor: "#2d6a4f",
  },
  {
    tier: "MEDIUM_SOLUTION" as const,
    heading: "ADAPTED APPROACHES",
    subtitle: "Modified from adjacent wins",
    accentColor: "#6b5b4f",
  },
  {
    tier: "HARD_EXPERIMENT" as const,
    heading: "EXPERIMENTAL OPPORTUNITIES",
    subtitle: "Novel approaches worth exploring",
    accentColor: "#c1272d",
  },
];

export default function UseCaseTierSection({ useCases, id }: UseCaseTierSectionProps) {
  const renderedSections = TIER_SECTIONS.filter(
    ({ tier }) => useCases.some((uc) => uc.tier === tier)
  );

  if (renderedSections.length === 0) return null;

  return (
    <div id={id} className="space-y-0">
      <div className="rule-double mb-6" />

      {TIER_SECTIONS.map(({ tier, heading, subtitle, accentColor }, idx) => {
        const items = useCases.filter((uc) => uc.tier === tier);
        if (items.length === 0) return null;

        return (
          <div key={tier}>
            {idx > 0 && <div className="rule-hairline my-8" />}

            {/* Tier heading block */}
            <div
              className="pl-4 mb-5"
              style={{ borderLeft: `2px solid ${accentColor}` }}
            >
              <h2
                className="font-label uppercase tracking-[0.12em] text-sm font-semibold"
                style={{ color: accentColor }}
              >
                {heading}
              </h2>
              <p className="font-body text-sm text-ink-light mt-0.5">{subtitle}</p>
            </div>

            {/* Use case entries */}
            <div className="space-y-0">
              {items.map((uc) => (
                <UseCaseCard key={uc.title} useCase={uc} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
