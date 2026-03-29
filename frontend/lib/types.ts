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
  feedback_history: ReportFeedback[]
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

// --- Multi-agent hypothesis system ---

export type HypothesisStatus =
  | 'forming'
  | 'testing'
  | 'validated'
  | 'rejected'
  | 'needs_user_input'

export interface TestResult {
  test_type: string
  finding: string
  impact_on_confidence: number
  evidence_ids: string[]
}

export interface ReasoningStep {
  step_type: string
  description: string
  evidence_ids: string[]
  confidence_delta: number
  timestamp?: string
}

export interface Hypothesis {
  hypothesis_id: string
  statement: string
  category: string
  target_process: string
  status: HypothesisStatus
  confidence: number
  evidence_for: string[]
  evidence_against: string[]
  evidence_conditions: string[]
  analogous_engagements: string[]
  conditions_for_success: string[]
  risks: string[]
  open_questions: string[]
  test_results: TestResult[]
  reasoning_chain: ReasoningStep[]
  formed_by_agent: string
  tested_by_agent: string
  parent_hypothesis_id?: string
}

export interface CompanyUnderstanding {
  company_name: string
  what_they_do: string
  how_they_make_money: string
  size_and_scale: string
  technology_landscape: string
  organizational_structure: string
  confidence: number
  evidence_ids: string[]
}

export interface IndustryContext {
  industry: string
  key_trends: string[]
  competitive_dynamics: string
  regulatory_landscape: string
  ai_adoption_level: string
  confidence: number
  evidence_ids: string[]
}

export interface PainPoint {
  pain_id: string
  description: string
  affected_process: string
  severity: string
  current_workaround: string
  evidence_ids: string[]
  confidence: number
}

export interface AgentState {
  agent_id: string
  agent_type: string
  status: string
  tool_calls_made: number
  tool_calls_budget: number
  evidence_produced: string[]
  started_at?: string
  completed_at?: string
  summary: string
}

export interface UserInteractionPoint {
  interaction_id: string
  run_id: string
  interaction_type: string
  message: string
  context: Record<string, unknown>
  agent_source: string
  requires_response: boolean
  response: string | null
}

export interface ReportOpportunity {
  title: string
  hypothesis_id: string
  narrative: string
  tier: string
  confidence: number
  roi_estimate?: Record<string, unknown>
  evidence_summary: string
  analogous_cases: Record<string, unknown>[]
  risks: string[]
  conditions_for_success: string[]
  recommended_approach: string
}

export interface AdaptiveReport {
  run_id: string
  executive_summary: string
  key_insight: string
  opportunities: ReportOpportunity[]
  reasoning_chain: string[]
  confidence_assessment: string
  what_we_dont_know: string[]
  recommended_next_steps: string[]
  evidence_annex: Record<string, unknown>[]
  agent_activity_summary: Record<string, unknown>[]
}

export interface ReportFeedback {
  feedback_type: 'edit' | 'deepen' | 'reinvestigate'
  target_section: string
  instruction: string
}
