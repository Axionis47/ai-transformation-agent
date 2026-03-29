import type {
  AgentState,
  AssumptionsDraft,
  CompanyIntake,
  EvidenceItem,
  Hypothesis,
  Opportunity,
  ReasoningConfig,
  ReportFeedback,
  Run,
  UIHints,
  UserInteractionPoint,
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface SystemDefaults {
  rag_budget: number
  search_budget: number
  search_max_calls: number
  reasoning_model: string
  synthesis_model: string
  pipeline_stages: string[]
}

export async function getDefaults(): Promise<SystemDefaults> {
  const res = await fetch(`${BASE}/v1/defaults`)
  if (!res.ok) throw new Error('Failed to fetch defaults')
  return res.json()
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`)
    return res.ok
  } catch { return false }
}

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

export async function getUIHints(runId: string): Promise<UIHints> {
  return apiFetch<UIHints>(`/runs/${runId}/ui`)
}

export async function startRun(runId: string): Promise<unknown> {
  return apiFetch<unknown>(`/runs/${runId}/start`, { method: 'POST' })
}

export async function confirmAssumptions(
  runId: string,
  body?: AssumptionsDraft,
): Promise<Run> {
  return apiFetch<Run>(`/runs/${runId}/assumptions/confirm`, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })
}

export async function answerQuestion(
  runId: string,
  questionId: string,
  answer: string,
): Promise<unknown> {
  return apiFetch<unknown>(`/runs/${runId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ question_id: questionId, answer_text: answer }),
  })
}

export async function synthesize(runId: string): Promise<unknown> {
  return apiFetch<unknown>(`/runs/${runId}/synthesize`, { method: 'POST' })
}

export async function publish(runId: string): Promise<Run> {
  return apiFetch<Run>(`/runs/${runId}/publish`, { method: 'POST' })
}

export async function getEvidence(runId: string): Promise<EvidenceItem[]> {
  return apiFetch<EvidenceItem[]>(`/runs/${runId}/evidence`)
}

export async function getReport(runId: string): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/runs/${runId}/report`)
}

export async function getOpportunities(runId: string): Promise<Opportunity[]> {
  return apiFetch<Opportunity[]>(`/runs/${runId}/opportunities`)
}

export async function getTrace(runId: string): Promise<Record<string, unknown>[]> {
  return apiFetch<Record<string, unknown>[]>(`/runs/${runId}/trace`)
}

export async function refineReport(
  runId: string,
  body: {
    corrections?: { field: string; new_value: string; reason?: string }[]
    removed_opportunity_ids?: string[]
    additional_context?: string
  },
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/runs/${runId}/refine`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
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

export async function getHypothesis(
  runId: string,
  hypothesisId: string,
): Promise<Hypothesis> {
  return apiFetch<Hypothesis>(
    `/runs/${runId}/hypotheses/${hypothesisId}`,
  )
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

export async function enrichRun(
  runId: string,
  inputs: import('./types').EnrichmentInput[],
): Promise<import('./types').EnrichResponse> {
  return apiFetch<import('./types').EnrichResponse>(`/runs/${runId}/enrich`, {
    method: 'POST',
    body: JSON.stringify({ inputs }),
  })
}
