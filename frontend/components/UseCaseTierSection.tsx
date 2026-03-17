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
    heading: "Proven Solutions",
    subtitle: "High confidence, low effort — implement first",
    accentColor: "#16a34a",
    accentBg: "#f0fdf4",
    accentBorder: "#bbf7d0",
    dot: "bg-green-500",
  },
  {
    tier: "MEDIUM_SOLUTION" as const,
    heading: "Achievable Opportunities",
    subtitle: "Strong ROI with moderate investment",
    accentColor: "#d97706",
    accentBg: "#fffbeb",
    accentBorder: "#fde68a",
    dot: "bg-amber-500",
  },
  {
    tier: "HARD_EXPERIMENT" as const,
    heading: "Frontier Experiments",
    subtitle: "High potential, requires significant capability building",
    accentColor: "#4f6df5",
    accentBg: "#eff6ff",
    accentBorder: "#bfdbfe",
    dot: "bg-blue-500",
  },
];

export default function UseCaseTierSection({ useCases, id }: UseCaseTierSectionProps) {
  return (
    <div id={id} className="neo-raised p-6 space-y-7">
      {/* Section header */}
      <div className="pb-4 border-b border-[#c4cad6]/50">
        <div className="flex items-center gap-3">
          <div className="w-1 h-5 rounded-full" style={{ background: "#4f6df5" }} />
          <h2 className="text-base font-bold tracking-tight" style={{ color: "#1e2433" }}>
            AI Use Cases
          </h2>
        </div>
      </div>

      {/* Tier groups */}
      {TIER_SECTIONS.map(({ tier, heading, subtitle, accentColor, accentBg, accentBorder, dot }) => {
        const items = useCases.filter((uc) => uc.tier === tier);
        if (items.length === 0) return null;
        return (
          <div key={tier} className="space-y-4">
            {/* Tier header pill */}
            <div
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl border"
              style={{
                background: accentBg,
                borderColor: accentBorder,
              }}
            >
              <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
              <div className="flex-1 min-w-0">
                <span className="text-sm font-bold" style={{ color: accentColor }}>
                  {heading}
                </span>
                <span className="text-xs text-gray-500 ml-2 hidden sm:inline">{subtitle}</span>
              </div>
              <span
                className="text-xs font-semibold px-2 py-0.5 rounded-full"
                style={{ background: accentColor + "18", color: accentColor }}
              >
                {items.length} {items.length === 1 ? "use case" : "use cases"}
              </span>
            </div>

            {/* Cards */}
            <div className="space-y-3 pl-0">
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
