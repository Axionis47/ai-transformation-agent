"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Header from "@/components/shell/Header";
import Sidebar from "@/components/shell/Sidebar";
import PhaseProgress from "@/components/PhaseProgress";
import RunPhaseContent from "@/components/RunPhaseContent";
import InteractionModal from "@/components/InteractionModal";
import Spinner from "@/components/ui/Spinner";
import {
  getRun,
  getAgentStates,
  getHypotheses,
  getInteractions,
  respondToInteraction,
  submitIntake,
} from "@/lib/api";
import type {
  Run,
  AgentState,
  Hypothesis,
  UserInteractionPoint,
  CompanyIntake,
  ReasoningConfig,
} from "@/lib/types";

const PHASES = [
  "INTAKE",
  "GROUNDING",
  "DEEP_RESEARCH",
  "HYPOTHESIS_FORMATION",
  "HYPOTHESIS_TESTING",
  "SYNTHESIS",
  "REVIEW",
  "PUBLISHED",
];
const ACTIVE_PHASES = [
  "grounding",
  "deep_research",
  "hypothesis_formation",
  "hypothesis_testing",
  "synthesis",
];
const AGENT_PHASES = ["grounding", "deep_research", "hypothesis_formation", "hypothesis_testing"];
const HYPOTHESIS_PHASES = ["hypothesis_formation", "hypothesis_testing"];
const TERMINAL = ["review", "published", "failed"];

export default function RunPage() {
  const params = useParams();
  const runId = params.id as string;
  const [run, setRun] = useState<Run | null>(null);
  const [agents, setAgents] = useState<AgentState[]>([]);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pendingInteraction, setPendingInteraction] = useState<UserInteractionPoint | null>(null);
  const [intakeLoading, setIntakeLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Read depth/threshold from run config (not hardcoded)
  const depth =
    (run?.config_snapshot?.reasoning as Record<string, number> | undefined)?.depth_budget ?? 5;
  const threshold =
    (run?.config_snapshot?.reasoning as Record<string, number> | undefined)?.confidence_threshold ??
    0.7;

  const fetchRun = useCallback(async () => {
    try {
      setRun(await getRun(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run");
    }
  }, [runId]);

  useEffect(() => {
    fetchRun();
  }, [fetchRun]);

  // Polling during active phases
  useEffect(() => {
    if (!run) return;
    const s = run.status.toLowerCase();
    if (TERMINAL.includes(s) || !ACTIVE_PHASES.includes(s)) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    async function poll() {
      try {
        const status = run!.status.toLowerCase();
        const freshRun = await getRun(runId);
        setRun(freshRun);
        if (AGENT_PHASES.includes(status)) setAgents(await getAgentStates(runId));
        if (HYPOTHESIS_PHASES.includes(status)) setHypotheses(await getHypotheses(runId));
        const interactions = await getInteractions(runId);
        const pending = interactions.find((i) => i.requires_response && !i.response);
        if (pending) setPendingInteraction(pending);
      } catch {
        /* polling errors are non-fatal */
      }
    }

    poll();
    intervalRef.current = setInterval(poll, 2000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [run?.status, runId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch hypotheses for terminal report phases (one-shot)
  useEffect(() => {
    if (!run) return;
    const s = run.status.toLowerCase();
    if (["synthesis", "report", "review", "published"].includes(s)) {
      getHypotheses(runId)
        .then(setHypotheses)
        .catch(() => {});
    }
  }, [run?.status, runId]);

  async function handleIntakeSubmit(data: CompanyIntake) {
    setIntakeLoading(true);
    setError(null);
    try {
      await submitIntake(runId, data);
      await fetchRun();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit intake");
    } finally {
      setIntakeLoading(false);
    }
  }

  if (!run)
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center">
        {error ? <p className="text-rose text-sm">{error}</p> : <Spinner size={24} />}
      </div>
    );

  const status = run.status.toLowerCase();
  const isActive = ACTIVE_PHASES.includes(status);

  return (
    <div className="min-h-screen bg-canvas">
      <Header run={run} agents={agents} />
      <div className="flex">
        <Sidebar run={run} agents={agents} />
        <main className="flex-1 min-w-0 p-6 lg:p-8 max-w-5xl">
          {error && (
            <div className="mb-6 bg-rose/10 border border-rose/30 rounded-md p-4">
              <p className="text-sm text-rose">{error}</p>
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
            await respondToInteraction(runId, pendingInteraction.interaction_id, response);
            setPendingInteraction(null);
          }}
          onDismiss={() => setPendingInteraction(null)}
        />
      )}
    </div>
  );
}
