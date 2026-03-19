"use client";

// SolutionCard: displays a single delivered solution from Library A (Tenex wins)

const INDUSTRY_BADGE: Record<string, { bg: string; text: string; border: string }> = {
  logistics:          { bg: "#eff6ff", text: "#2563eb", border: "#bfdbfe" },
  financial_services: { bg: "#faf5ff", text: "#7c3aed", border: "#ddd6fe" },
  healthcare:         { bg: "#f0fdf4", text: "#16a34a", border: "#bbf7d0" },
  retail:             { bg: "#fdf4ff", text: "#a21caf", border: "#f0abfc" },
  manufacturing:      { bg: "#fff7ed", text: "#c2410c", border: "#fed7aa" },
  default:            { bg: "#f8fafc", text: "#475569", border: "#e2e8f0" },
};

const SIZE_BADGE: Record<string, { bg: string; text: string }> = {
  startup:    { bg: "#f0fdf4", text: "#15803d" },
  "mid-market": { bg: "#fffbeb", text: "#b45309" },
  enterprise: { bg: "#eff6ff", text: "#1d4ed8" },
};

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
    INDUSTRY_BADGE[solution.industry] ?? INDUSTRY_BADGE.default;
  const sizeStyle =
    SIZE_BADGE[solution.company_profile.size_label] ?? SIZE_BADGE["mid-market"];

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
          style={{ background: "#f1f5f9", color: "#64748b" }}
        >
          {solution.maturity_at_engagement}
        </span>
      </div>

      {/* Title */}
      <h3
        className="text-sm font-bold leading-snug"
        style={{ color: "#1e2433" }}
      >
        {solution.engagement_title}
      </h3>

      {/* Primary metric — visually prominent */}
      <div
        className="rounded-xl px-4 py-3 border"
        style={{ background: "#f0fdf4", borderColor: "#bbf7d0" }}
      >
        <p
          className="text-[10px] font-semibold uppercase tracking-widest mb-1"
          style={{ color: "#16a34a" }}
        >
          {solution.results.primary_metric.label}
        </p>
        <p
          className="text-lg font-extrabold"
          style={{ color: "#15803d" }}
        >
          {solution.results.primary_metric.value}
        </p>
      </div>

      {/* Footer row */}
      <div className="flex items-center justify-between gap-2 mt-auto pt-1">
        <span
          className="text-[11px] font-medium px-2.5 py-1 rounded-full border"
          style={{ background: "#f8fafc", color: "#475569", borderColor: "#e2e8f0" }}
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
