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
    sectionName: "Delivered",
    heading: "Delivered Solutions",
    subtitle: "Tenex has built this — proven results from past engagements",
    icon: "✓",
    accentColor: "#16a34a",
    accentBg: "#f0fdf4",
    accentBorder: "#bbf7d0",
    borderClass: "border-l-4 border-green-500",
    iconBg: "#dcfce7",
  },
  {
    tier: "MEDIUM_SOLUTION" as const,
    sectionName: "Adaptation",
    heading: "Adapted Solutions",
    subtitle: "Tenex has built something close — adapted for your context",
    icon: "⚙",
    accentColor: "#d97706",
    accentBg: "#fffbeb",
    accentBorder: "#fde68a",
    borderClass: "border-l-4 border-amber-500",
    iconBg: "#fef3c7",
  },
  {
    tier: "HARD_EXPERIMENT" as const,
    sectionName: "Ambitious",
    heading: "Ambitious Opportunities",
    subtitle: "Your industry is doing this — we could build it",
    icon: "↗",
    accentColor: "#4f6df5",
    accentBg: "#eff6ff",
    accentBorder: "#bfdbfe",
    borderClass: "border-l-4 border-blue-500",
    iconBg: "#dbeafe",
  },
];

export default function UseCaseTierSection({ useCases, id }: UseCaseTierSectionProps) {
  const renderedSections = TIER_SECTIONS.filter(
    ({ tier }) => useCases.some((uc) => uc.tier === tier)
  );

  return (
    <div id={id} className="space-y-6">
      {/* Page section header */}
      <div className="neo-raised px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-1 h-5 rounded-full" style={{ background: "#4f6df5" }} />
          <h2 className="text-base font-bold tracking-tight" style={{ color: "#1e2433" }}>
            AI Use Cases
          </h2>
          <span className="text-xs text-gray-400 ml-1">
            {renderedSections.length} {renderedSections.length === 1 ? "section" : "sections"}
          </span>
        </div>
      </div>

      {/* Tier sections */}
      {TIER_SECTIONS.map(
        ({ tier, sectionName, heading, subtitle, icon, accentColor, accentBg, accentBorder, borderClass, iconBg }) => {
          const items = useCases.filter((uc) => uc.tier === tier);
          if (items.length === 0) return null;

          return (
            <div key={tier} className={`neo-raised overflow-hidden ${borderClass}`}>
              {/* Tier section header */}
              <div
                className="px-6 py-4 border-b"
                style={{ background: accentBg, borderColor: accentBorder }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span
                      className="flex items-center justify-center w-8 h-8 rounded-full text-base font-bold shrink-0"
                      style={{ background: iconBg, color: accentColor }}
                      aria-hidden="true"
                    >
                      {icon}
                    </span>
                    <div>
                      <h3 className="text-base font-bold leading-tight" style={{ color: accentColor }}>
                        {heading}
                      </h3>
                      <p className="text-xs mt-0.5" style={{ color: "#6b7280" }}>
                        {subtitle}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 mt-0.5">
                    <span
                      className="text-xs font-semibold px-2.5 py-1 rounded-full"
                      style={{ background: accentColor + "18", color: accentColor }}
                    >
                      {items.length} {items.length === 1 ? "recommendation" : "recommendations"}
                    </span>
                    <span
                      className="text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded border"
                      style={{ color: accentColor, borderColor: accentBorder, background: "white" }}
                    >
                      {sectionName}
                    </span>
                  </div>
                </div>
              </div>

              {/* Cards */}
              <div className="p-5 space-y-4">
                {items.map((uc) => (
                  <UseCaseCard key={uc.title} useCase={uc} />
                ))}
              </div>
            </div>
          );
        }
      )}
    </div>
  );
}
