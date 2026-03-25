export interface BudgetConfig {
  external_search_query_budget: number
  external_search_max_calls: number
  rag_query_budget: number
  rag_top_k: number
  rag_min_score: number
}

export interface BudgetState {
  external_search_queries_used: number
  external_search_calls_used: number
  rag_queries_used: number
}

export interface CompanyIntake {
  company_name: string
  industry: string
  employee_count_band?: string
  notes?: string
  constraints: string[]
}

export interface ReasoningConfig {
  reasoning_depth: number
  confidence_threshold: number
}

export interface Assumption {
  field: string
  value: string
  confidence: number
  source: string
}

export interface AssumptionsDraft {
  assumptions: Assumption[]
  open_questions: string[]
}

export interface UserQuestion {
  question_id: string
  run_id: string
  field: string
  question_text: string
  context?: string
}

export interface EvidenceItem {
  evidence_id: string
  run_id: string
  source_type: string
  source_ref: string
  title: string
  uri?: string
  snippet: string
  relevance_score: number
  confidence_score?: number
  retrieval_meta: Record<string, unknown>
}

export interface ReasoningState {
  current_loop: number
  evidence_ids: string[]
  field_coverage: Record<string, number>
  overall_confidence: number
  pending_question: UserQuestion | null
  completed: boolean
  stop_reason?: string
  coverage_gaps: string[]
  loops_completed: number
  escalation_reason?: string
  escalation_fields: string[]
  contradictions: { field?: string; values?: string[] }[]
  confidence_history: number[]
}

export interface Opportunity {
  opportunity_id: string
  run_id: string
  template_id: string
  name: string
  description: string
  tier: string
  feasibility: number
  roi: number
  time_to_value: number
  confidence: number
  evidence_ids: string[]
  assumptions: Record<string, unknown>
  rationale: string
  adaptation_needed?: string
  risks: string[]
  data_sufficiency: 'scored' | 'insufficient_data'
}

export interface Run {
  run_id: string
  status: string
  created_at: string
  config_snapshot: Record<string, unknown>
  budgets: BudgetConfig
  budget_state: BudgetState
  company_intake: CompanyIntake | null
  assumptions: AssumptionsDraft | null
  evidence: EvidenceItem[]
  reasoning_state: ReasoningState | null
  opportunities: Opportunity[]
  report: Record<string, unknown>
}

export interface UIAction {
  id: string
  label: string
  endpoint: string
  method: string
  enabled: boolean
  confirm: boolean
}

export interface EditableField {
  path: string
  label: string
  field_type: string
  default?: string
  constraints: Record<string, unknown>
}

export interface BudgetView {
  rag_queries_remaining: number
  external_search_queries_remaining: number
  total_cost_estimate: string
}

export interface UIHints {
  stage_title: string
  stage_description: string
  progress: { stage: string; status: string }[]
  actions: UIAction[]
  editable_fields: EditableField[]
  budget_view: BudgetView
  agent_message?: string
}
