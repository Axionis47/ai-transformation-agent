"use client";

import Link from "next/link";
import type {
  Run,
  AgentState,
  Hypothesis,
  CompanyIntake,
} from "@/lib/types";
import AgentActivityPanel from "@/components/AgentActivityPanel";
import HypothesisList from "@/components/HypothesisList";
import IntakeForm from "@/components/IntakeForm";
import Badge from "@/components/ui/Badge";
import SectionTitle from "@/components/phases/SectionTitle";
import SummaryStats from "@/components/phases/SummaryStats";
import CompanyUnderstandingPanel from "@/components/phases/CompanyUnderstandingPanel";
import IndustryContextPanel from "@/components/phases/IndustryContextPanel";
import PainPointsPanel from "@/components/phases/PainPointsPanel";

interface RunPhaseContentProps {
  run: Run;
  agents: AgentState[];
  hypotheses: Hypothesis[];
  onIntakeSubmit: (data: CompanyIntake) => void;
  intakeLoading: boolean;
  depth: number;
  threshold: number;
}

export default function RunPhaseContent({
  run,
  agents,
  hypotheses,
  onIntakeSubmit,
  intakeLoading,
  depth,
  threshold,
}: RunPhaseContentProps) {
  const status = run.status.toLowerCase();
  const runId = run.run_id;

  // INTAKE — if intake already saved, show waiting state
  if (status === "intake" || status === "created") {
    if (run.company_intake?.company_name) {
      return (
        <div className="max-w-3xl mx-auto text-center py-12">
          <SectionTitle
            title="Starting Analysis"
            subtitle={`Analyzing ${run.company_intake.company_name}...`}
          />
          <div className="flex items-center justify-center gap-3 mt-4">
            <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
            <span className="text-sm text-ink-secondary font-mono">
              Initializing multi-agent pipeline
            </span>
          </div>
        </div>
      );
    }
    return (
      <div className="max-w-3xl mx-auto">
        <SectionTitle
          title="Company Intake"
          subtitle="Provide company details to begin analysis."
        />
        <IntakeForm
          onSubmit={(data) => onIntakeSubmit(data)}
          loading={intakeLoading}
          depth={depth}
          threshold={threshold}
          onDepthChange={() => {}}
          onThresholdChange={() => {}}
        />
      </div>
    );
  }

  // GROUNDING
  if (status === "grounding") {
    return (
      <>
        <SectionTitle
          title="Researching Company & Industry"
          subtitle="CompanyProfiler and IndustryAnalyst running in parallel..."
        />
        <AgentActivityPanel agents={agents} />
        <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-4">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
            <span className="text-sm text-ink-secondary font-mono">
              {run.evidence.length} evidence items collected
            </span>
          </div>
        </div>
        <CompanyUnderstandingPanel run={run} />
        <IndustryContextPanel run={run} />
      </>
    );
  }

  // DEEP RESEARCH
  if (status === "deep_research") {
    return (
      <>
        <SectionTitle
          title="Investigating Pain Points"
          subtitle="PainInvestigator analyzing operational gaps..."
        />
        <AgentActivityPanel agents={agents} />
        <div className="mt-6 bg-canvas-raised border border-edge-subtle rounded-md p-4">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
            <span className="text-sm text-ink-secondary font-mono">
              {run.evidence.length} evidence items
            </span>
          </div>
        </div>
        <CompanyUnderstandingPanel run={run} />
        <IndustryContextPanel run={run} />
        <PainPointsPanel run={run} />
      </>
    );
  }

  // HYPOTHESIS FORMATION
  if (status === "hypothesis_formation") {
    return (
      <>
        <SectionTitle
          title="Forming Hypotheses"
          subtitle="Generating transformation hypotheses from evidence..."
        />
        <AgentActivityPanel agents={agents} />
        <CompanyUnderstandingPanel run={run} />
        <PainPointsPanel run={run} />
        {hypotheses.length > 0 && (
          <div className="mt-6">
            <HypothesisList hypotheses={hypotheses} />
          </div>
        )}
      </>
    );
  }

  // HYPOTHESIS TESTING
  if (status === "hypothesis_testing") {
    const testing = agents.filter((a) => a.status === "running").length;
    return (
      <>
        <SectionTitle
          title="Testing Hypotheses"
          subtitle={
            testing > 0
              ? `${testing} testers running in parallel...`
              : "Evaluating hypothesis validity..."
          }
        />
        <AgentActivityPanel agents={agents} />
        <div className="mt-6">
          <HypothesisList hypotheses={hypotheses} />
        </div>
      </>
    );
  }

  // SYNTHESIS / REPORT / REVIEW / PUBLISHED
  if (["synthesis", "report", "review", "published"].includes(status)) {
    return (
      <>
        <SectionTitle title={status === "published" ? "Analysis Published" : "Analysis Complete"} />
        {status === "published" && (
          <div className="flex items-center gap-2 mb-6">
            <Badge variant="mint">Published</Badge>
          </div>
        )}

        {/* Call to action */}
        <div className="mb-8 flex items-center gap-3">
          <Link
            href={`/run/${runId}/report`}
            className="inline-flex items-center gap-2 bg-mint text-ink-inverse px-6 py-3 text-sm font-semibold rounded-md hover:bg-mint-bright transition-colors"
          >
            View Full Report
          </Link>
          <Link
            href={`/run/${runId}/enrich`}
            className="inline-flex items-center gap-2 bg-transparent border border-indigo text-indigo px-6 py-3 text-sm font-semibold rounded-md hover:bg-indigo/10 transition-colors"
          >
            Enrich with Ground Truth
          </Link>
        </div>

        {/* Summary stats */}
        <SummaryStats hypotheses={hypotheses} evidenceCount={run.evidence.length} />

        {/* What the system learned */}
        <CompanyUnderstandingPanel run={run} />
        <IndustryContextPanel run={run} />
        <PainPointsPanel run={run} />

        {/* Hypotheses */}
        {hypotheses.length > 0 && (
          <div className="mt-6">
            <HypothesisList hypotheses={hypotheses} />
          </div>
        )}
      </>
    );
  }

  // FAILED
  if (status === "failed") {
    return (
      <div className="bg-rose/10 border border-rose/30 rounded-md p-6 text-center">
        <p className="text-sm text-rose font-medium">This analysis run has failed.</p>
      </div>
    );
  }

  return (
    <div className="bg-canvas-raised border border-edge-subtle rounded-md p-6 text-center">
      <p className="text-sm text-ink-tertiary">Phase: {run.status}</p>
    </div>
  );
}
