"use client";

// SolutionCard: displays a single delivered solution from Library A (Tenex wins)

import {
  INDUSTRY_BADGE_COLORS,
  SIZE_BADGE_COLORS,
  SOLUTIONS_ACCENT,
} from "@/lib/config";

export interface SolutionRecord {
  id: string;
  engagement_title: string;
  industry: string;
  company_profile: {
    size_label: string;
  };
  results: {
    primary_metric: {
      label: string;
      value: string;
    };
  };
  solution_category: string;
  engagement_details: {
    duration_months: number;
  };
  maturity_at_engagement: string;
}

interface SolutionCardProps {
  solution: SolutionRecord;
}

export default function SolutionCard({ solution }: SolutionCardProps) {
  const industryStyle =
    INDUSTRY_BADGE_COLORS[solution.industry] ?? INDUSTRY_BADGE_COLORS.default;
  const sizeStyle =
    SIZE_BADGE_COLORS[solution.company_profile.size_label] ?? SIZE_BADGE_COLORS["mid-market"];

  return (
    <div className="neo-flat p-5 space-y-4 border-l-[3px] border-green-500 flex flex-col">
      {/* Header badges row */}
      <div className="flex flex-wrap items-center gap-2">
        <span
          className="text-[11px] font-semibold px-2 py-0.5 rounded-full border"
          style={{
            background: industryStyle.bg,
            color: industryStyle.text,
            borderColor: industryStyle.border,
          }}
        >
          {solution.industry.replace("_", " ")}
        </span>
        <span
          className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
          style={{
            background: sizeStyle.bg,
            color: sizeStyle.text,
          }}
        >
          {solution.company_profile.size_label}
        </span>
        <span
          className="text-[11px] font-medium px-2 py-0.5 rounded-full"
          style={{ background: SOLUTIONS_ACCENT.maturityBg, color: SOLUTIONS_ACCENT.maturityText }}
        >
          {solution.maturity_at_engagement}
        </span>
      </div>

      {/* Title */}
      <h3
        className="text-sm font-bold leading-snug"
        style={{ color: SOLUTIONS_ACCENT.darkText }}
      >
        {solution.engagement_title}
      </h3>

      {/* Primary metric — visually prominent */}
      <div
        className="rounded-xl px-4 py-3 border"
        style={{ background: SOLUTIONS_ACCENT.metricBg, borderColor: SOLUTIONS_ACCENT.metricBorder }}
      >
        <p
          className="text-[10px] font-semibold uppercase tracking-widest mb-1"
          style={{ color: SOLUTIONS_ACCENT.green }}
        >
          {solution.results.primary_metric.label}
        </p>
        <p
          className="text-lg font-extrabold"
          style={{ color: SOLUTIONS_ACCENT.metricText }}
        >
          {solution.results.primary_metric.value}
        </p>
      </div>

      {/* Footer row */}
      <div className="flex items-center justify-between gap-2 mt-auto pt-1">
        <span
          className="text-[11px] font-medium px-2.5 py-1 rounded-full border"
          style={{
            background: SOLUTIONS_ACCENT.neutralBg,
            color: SOLUTIONS_ACCENT.neutralText,
            borderColor: SOLUTIONS_ACCENT.neutralBorder,
          }}
        >
          {solution.solution_category.replace("_", " ")}
        </span>
        <span className="text-[11px] text-gray-400">
          {solution.engagement_details.duration_months} month engagement
        </span>
      </div>
    </div>
  );
}
