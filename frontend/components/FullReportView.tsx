"use client";

import type { AnalyzeSuccess } from "@/lib/types";
import ReportCard from "@/components/ReportCard";
import UseCaseTierSection from "@/components/UseCaseTierSection";

interface FullReportViewProps {
  data: AnalyzeSuccess;
}

export default function FullReportView({ data }: FullReportViewProps) {
  return (
    <div className="py-4">
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
          signals={data.signals?.signals}
          matchResults={[
            ...(data.match_results?.delivered ?? []),
            ...(data.match_results?.adaptation ?? []),
            ...(data.match_results?.ambitious ?? []),
          ]}
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
    </div>
  );
}
