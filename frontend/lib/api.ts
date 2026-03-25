import type {
  AssumptionsDraft,
  CompanyIntake,
  EvidenceItem,
  Opportunity,
  ReasoningConfig,
  Run,
  UIHints,
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
