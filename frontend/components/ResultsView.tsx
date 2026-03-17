"use client";

import Link from "next/link";
import type { AnalyzeSuccess } from "@/lib/types";
import ReportCard from "@/components/ReportCard";
import MaturityBadge from "@/components/MaturityBadge";
import UseCaseTierSection from "@/components/UseCaseTierSection";
import TracePanel from "@/components/TracePanel";
import ReportNav from "@/components/ReportNav";

interface ResultsViewProps {
  data: AnalyzeSuccess;
}

function buildDimensions(data: AnalyzeSuccess): Record<string, number> | undefined {
  if (data.maturity?.dimensions) {
    return Object.fromEntries(
      Object.entries(data.maturity.dimensions).map(([k, v]) => [k, v.score])
    );
  }
  return undefined;
}

export default function ResultsView({ data }: ResultsViewProps) {
  return (
    <div className="space-y-6 page-fade-in">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <ReportNav />
        <Link
          href="/"
          className="neo-flat px-5 py-2 text-xs font-medium text-gray-500 rounded-xl transition-all hover:text-gray-700 active:shadow-neo-btn-pressed focus:outline-none focus-visible:ring-2 focus-visible:ring-[#4f6df5]"
        >
          + New Analysis
        </Link>
      </div>
      <MaturityBadge
        score={data.maturity.composite_score}
        label={data.maturity.composite_label}
        elapsedSeconds={data.elapsed_seconds}
        costUsd={data.cost_usd}
        dimensions={buildDimensions(data)}
      />
      <ReportCard
        id="section-exec-summary"
        title="Executive Summary"
        content={data.report.exec_summary}
        wins={data.victory_matches}
      />
      <ReportCard
        id="section-current-state"
        title="Current State"
        content={data.report.current_state}
      />
      {data.use_cases && data.use_cases.length > 0 ? (
        <UseCaseTierSection
          id="section-use-cases"
          useCases={data.use_cases}
        />
      ) : (
        <ReportCard
          id="section-use-cases"
          title="AI Use Cases"
          content={data.report.use_cases}
          wins={data.victory_matches}
        />
      )}
      <ReportCard
        id="section-roi"
        title="ROI Analysis"
        content={data.report.roi_analysis}
      />
      <ReportCard
        id="section-roadmap"
        title="Transformation Roadmap"
        content={data.report.roadmap}
      />
      <TracePanel runId={data.run_id} />
    </div>
  );
}
