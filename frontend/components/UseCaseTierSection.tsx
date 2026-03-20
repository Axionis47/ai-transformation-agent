"use client";

import type { TieredUseCase } from "@/lib/types";
import UseCaseCard from "@/components/UseCaseCard";
import { USE_CASE_TIERS } from "@/lib/config";

interface UseCaseTierSectionProps {
  useCases: TieredUseCase[];
  id?: string;
}

type TierKey = keyof typeof USE_CASE_TIERS;

const TIER_ORDER: TierKey[] = ["LOW_HANGING_FRUIT", "MEDIUM_SOLUTION", "HARD_EXPERIMENT"];

export default function UseCaseTierSection({ useCases, id }: UseCaseTierSectionProps) {
  const renderedTiers = TIER_ORDER.filter(
    (tier) => useCases.some((uc) => uc.tier === tier)
  );

  if (renderedTiers.length === 0) return null;

  return (
    <div id={id} className="space-y-0">
      <div className="rule-double mb-6" />

      {TIER_ORDER.map((tier, idx) => {
        const items = useCases.filter((uc) => uc.tier === tier);
        if (items.length === 0) return null;
        const { heading, subtitle, accent } = USE_CASE_TIERS[tier];

        return (
          <div key={tier}>
            {idx > 0 && <div className="rule-hairline my-8" />}

            {/* Tier heading block */}
            <div
              className="pl-4 mb-5"
              style={{ borderLeft: `2px solid ${accent}` }}
            >
              <h2
                className="font-label uppercase tracking-[0.12em] text-sm font-semibold"
                style={{ color: accent }}
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
