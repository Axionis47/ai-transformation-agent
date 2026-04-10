import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { POLL_INTERVAL_MS, ACTIVE_PHASES, AGENT_PHASES, HYPOTHESIS_PHASES } from "@/config/constants";
import * as api from "./api";
import type { SystemDefaults } from "./api";
import type {
  Run,
  AgentState,
  Hypothesis,
  UserInteractionPoint,
  CompanyIntake,
  EvidenceItem,
  AdaptiveReport,
  ReportFeedback,
  EnrichmentInput,
  EnrichResponse,
} from "./types";

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

export function useRun(runId: string) {
  return useQuery<Run>({
    queryKey: ["run", runId],
    queryFn: () => api.getRun(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status?.toLowerCase();
      return status && ACTIVE_PHASES.includes(status) ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useAgentStates(runId: string, enabled: boolean) {
  return useQuery<AgentState[]>({
    queryKey: ["agents", runId],
    queryFn: () => api.getAgentStates(runId),
    enabled,
    refetchInterval: (query) => {
      // Only poll when the parent hook says we're enabled (active agent phase)
      return enabled ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useHypotheses(runId: string, enabled: boolean) {
  return useQuery<Hypothesis[]>({
    queryKey: ["hypotheses", runId],
    queryFn: () => api.getHypotheses(runId),
    enabled,
    refetchInterval: (query) => {
      return enabled ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useInteractions(runId: string, enabled: boolean) {
  return useQuery<UserInteractionPoint[]>({
    queryKey: ["interactions", runId],
    queryFn: () => api.getInteractions(runId),
    enabled,
    refetchInterval: (query) => {
      return enabled ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useTrace(runId: string) {
  return useQuery({
    queryKey: ["trace", runId],
    queryFn: async () => {
      const [trace, agents] = await Promise.all([
        api.getTrace(runId),
        api.getAgentStates(runId).catch(() => [] as AgentState[]),
      ]);
      return { trace, agents };
    },
  });
}

export function useReport(runId: string) {
  return useQuery({
    queryKey: ["report", runId],
    queryFn: async () => {
      const [run, report, evidence] = await Promise.all([
        api.getRun(runId),
        api.getReport(runId),
        api.getEvidence(runId).catch(() => [] as EvidenceItem[]),
      ]);
      let adaptiveReport: AdaptiveReport | null = null;
      if (report && typeof (report as Record<string, unknown>).key_insight === "string" && Array.isArray((report as Record<string, unknown>).opportunities)) {
        adaptiveReport = report as unknown as AdaptiveReport;
      }
      return { run, report: adaptiveReport, evidence };
    },
  });
}

export function useDefaults() {
  return useQuery<SystemDefaults>({
    queryKey: ["defaults"],
    queryFn: () => api.getDefaults(),
    staleTime: Infinity,
  });
}

export function useHealth() {
  return useQuery<boolean>({
    queryKey: ["health"],
    queryFn: () => api.checkHealth(),
    staleTime: Infinity,
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

export function useSubmitIntake(runId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (intake: CompanyIntake) => api.submitIntake(runId, intake),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", runId] });
    },
  });
}

export function useRespondToInteraction(runId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ interactionId, response }: { interactionId: string; response: string }) =>
      api.respondToInteraction(runId, interactionId, response),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interactions", runId] });
    },
  });
}

export function useApproveReport(runId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.approveReport(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", runId] });
      queryClient.invalidateQueries({ queryKey: ["report", runId] });
    },
  });
}

export function useInvestigateDeeper(runId: string) {
  return useMutation({
    mutationFn: () => api.requestDeeperInvestigation(runId),
  });
}

export function useRefineReport(runId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (feedbacks: ReportFeedback[]) => api.refineReportWithFeedback(runId, feedbacks),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["report", runId] });
      queryClient.invalidateQueries({ queryKey: ["run", runId] });
    },
  });
}

export function useEnrich(runId: string) {
  const queryClient = useQueryClient();
  return useMutation<EnrichResponse, Error, EnrichmentInput[]>({
    mutationFn: (inputs: EnrichmentInput[]) => api.enrichRun(runId, inputs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", runId] });
      queryClient.invalidateQueries({ queryKey: ["hypotheses", runId] });
    },
  });
}
