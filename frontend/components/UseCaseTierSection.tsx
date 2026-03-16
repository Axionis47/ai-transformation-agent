"use client";

import type { TieredUseCase } from "@/lib/types";
import UseCaseCard from "@/components/UseCaseCard";

interface UseCaseTierSectionProps {
  useCases: TieredUseCase[];
}

const TIER_SECTIONS = [
  {
    tier: "LOW_HANGING_FRUIT" as const,
    heading: "Proven Solutions",
    headingColor: "text-green-700",
    borderColor: "border-green-200",
  },
  {
    tier: "MEDIUM_SOLUTION" as const,
    heading: "Achievable Opportunities",
    headingColor: "text-amber-700",
    borderColor: "border-amber-200",
  },
  {
    tier: "HARD_EXPERIMENT" as const,
    heading: "Frontier Experiments",
    headingColor: "text-blue-700",
    borderColor: "border-blue-200",
  },
];

export default function UseCaseTierSection({ useCases }: UseCaseTierSectionProps) {
  return (
    <div className="neo-raised p-6 space-y-6">
      <h2 className="text-base font-semibold text-gray-700 uppercase tracking-widest pb-3 border-b border-neo-dark/20">
        AI Use Cases
      </h2>
      {TIER_SECTIONS.map(({ tier, heading, headingColor, borderColor }) => {
        const items = useCases.filter((uc) => uc.tier === tier);
        if (items.length === 0) return null;
        return (
          <div key={tier} className={`space-y-3 pt-2 border-t ${borderColor}`}>
            <h3 className={`text-sm font-semibold ${headingColor}`}>{heading}</h3>
            {items.map((uc) => (
              <UseCaseCard key={uc.title} useCase={uc} />
            ))}
          </div>
        );
      })}
    </div>
  );
}
