"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Header from "@/components/shell/Header";
import Sidebar from "@/components/shell/Sidebar";
import PhaseProgress from "@/components/PhaseProgress";
import RunPhaseContent from "@/components/RunPhaseContent";
import InteractionModal from "@/components/InteractionModal";
import Spinner from "@/components/ui/Spinner";
import { submitIntake } from "@/lib/api";
import { useRun, useAgentStates, useHypotheses, useInteractions, useRespondToInteraction } from "@/lib/hooks";
import type { CompanyIntake } from "@/lib/types";
import {
  PHASES,
  ACTIVE_PHASES,
  AGENT_PHASES,
  HYPOTHESIS_PHASES,
  POLL_INTERVAL_MS,
} from "@/config/constants";

export default function RunPage() {
  const params = useParams();
  const runId = params.id as string;
  const [error, setError] = useState<string | null>(null);
  const [intakeLoading, setIntakeLoading] = useState(false);

  const { data: run, error: runError } = useRun(runId);

  const status = run?.status.toLowerCase() ?? "";
  const isActive = ACTIVE_PHASES.includes(status);
  const isAgentPhase = AGENT_PHASES.includes(status);
  const isHypothesisPhase =
    HYPOTHESIS_PHASES.includes(status) ||
    ["synthesis", "report", "review", "published"].includes(status);

  const { data: agents = [] } = useAgentStates(runId, isAgentPhase);
  const { data: hypotheses = [] } = useHypotheses(runId, isHypothesisPhase);
  const { data: interactions = [] } = useInteractions(runId, isActive);
  const respondMutation = useRespondToInteraction(runId);

  const pendingInteraction = interactions.find((i) => i.requires_response && !i.response) ?? null;

  // Read depth/threshold from run config (not hardcoded)
  const depth =
    (run?.config_snapshot?.reasoning as Record<string, number> | undefined)?.depth_budget ?? 5;
  const threshold =
    (run?.config_snapshot?.reasoning as Record<string, number> | undefined)?.confidence_threshold ??
    0.7;

  async function handleIntakeSubmit(data: CompanyIntake) {
    setIntakeLoading(true);
    setError(null);
    try {
      await submitIntake(runId, data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit intake");
    } finally {
      setIntakeLoading(false);
    }
  }

  const displayError = error || (runError instanceof Error ? runError.message : null);

  if (!run)
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center">
        {displayError ? <p className="text-rose text-sm">{displayError}</p> : <Spinner size={24} />}
      </div>
    );

  return (
    <div className="min-h-screen bg-canvas">
      <Header run={run} agents={agents} />
      <div className="flex">
        <Sidebar run={run} agents={agents} />
        <main className="flex-1 min-w-0 p-6 lg:p-8 max-w-5xl">
          {displayError && (
            <div className="mb-6 bg-rose/10 border border-rose/30 rounded-md p-4">
              <p className="text-sm text-rose">{displayError}</p>
            </div>
          )}

          {isActive && (
            <section className="mb-8">
              <PhaseProgress currentPhase={run.status} phases={PHASES} />
            </section>
          )}

          <RunPhaseContent
            run={run}
            agents={agents}
            hypotheses={hypotheses}
            onIntakeSubmit={handleIntakeSubmit}
            intakeLoading={intakeLoading}
            depth={depth}
            threshold={threshold}
          />
        </main>
      </div>

      {pendingInteraction && (
        <InteractionModal
          interaction={pendingInteraction}
          onRespond={async (response) => {
            await respondMutation.mutateAsync({
              interactionId: pendingInteraction.interaction_id,
              response,
            });
          }}
          onDismiss={() => {
            /* dismiss handled by next poll clearing the pending interaction */
          }}
        />
      )}
    </div>
  );
}
