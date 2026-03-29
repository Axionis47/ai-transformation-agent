import type {
  AgentState,
  CompanyIntake,
  EvidenceItem,
  Hypothesis,
  ReasoningConfig,
  ReportFeedback,
  Run,
  UserInteractionPoint,
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export async function createRun(
  company_name: string,
  industry: string,
  reasoningConfig?: ReasoningConfig,
): Promise<Run> {
  return apiFetch<Run>('/runs', {
    method: 'POST',
    body: JSON.stringify({
      company_name,
      industry,
      reasoning_depth: reasoningConfig?.reasoning_depth,
      confidence_threshold: reasoningConfig?.confidence_threshold,
    }),
  })
}

export async function getRun(runId: string): Promise<Run> {
  return apiFetch<Run>(`/runs/${runId}`)
}

export async function submitIntake(
  runId: string,
  intake: CompanyIntake,
): Promise<Run> {
  return apiFetch<Run>(`/runs/${runId}/company-intake`, {
    method: 'PUT',
    body: JSON.stringify(intake),
  })
}

export async function getEvidence(runId: string): Promise<EvidenceItem[]> {
  return apiFetch<EvidenceItem[]>(`/runs/${runId}/evidence`)
}

export async function getReport(runId: string): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/runs/${runId}/report`)
}

export async function getTrace(runId: string): Promise<Record<string, unknown>[]> {
  return apiFetch<Record<string, unknown>[]>(`/runs/${runId}/trace`)
}

// --- Multi-agent endpoints ---

export async function getAgentStates(runId: string): Promise<AgentState[]> {
  const res = await apiFetch<{ agents: AgentState[]; count: number }>(
    `/runs/${runId}/agents`,
  )
  return res.agents
}

export async function getHypotheses(runId: string): Promise<Hypothesis[]> {
  const res = await apiFetch<{ hypotheses: Hypothesis[]; count: number }>(
    `/runs/${runId}/hypotheses`,
  )
  return res.hypotheses
}

export async function getInteractions(
  runId: string,
): Promise<UserInteractionPoint[]> {
  const res = await apiFetch<{
    interactions: UserInteractionPoint[]
    pending: number
    resolved: number
  }>(`/runs/${runId}/interactions`)
  return res.interactions
}

export async function respondToInteraction(
  runId: string,
  interactionId: string,
  response: string,
): Promise<UserInteractionPoint> {
  return apiFetch<UserInteractionPoint>(
    `/runs/${runId}/interactions/${interactionId}/respond`,
    {
      method: 'POST',
      body: JSON.stringify({
        interaction_id: interactionId,
        response,
      }),
    },
  )
}

export async function approveReport(
  runId: string,
): Promise<{ run_id: string; status: string; message: string }> {
  return apiFetch<{ run_id: string; status: string; message: string }>(
    `/runs/${runId}/review/approve`,
    { method: 'POST' },
  )
}

export async function requestDeeperInvestigation(
  runId: string,
): Promise<{ run_id: string; status: string; message: string }> {
  return apiFetch<{ run_id: string; status: string; message: string }>(
    `/runs/${runId}/review/investigate`,
    { method: 'POST' },
  )
}

export async function refineReportWithFeedback(
  runId: string,
  feedbacks: ReportFeedback[],
): Promise<Run> {
  return apiFetch<Run>(`/runs/${runId}/report/refine`, {
    method: 'POST',
    body: JSON.stringify({ feedbacks }),
  })
}
