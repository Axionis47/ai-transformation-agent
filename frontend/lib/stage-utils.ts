import { STAGE_ORDER } from "@/config/constants";

export type StageStatusValue = "active" | "completed" | "pending";

export function stageStatus(runStatus: string, targetStages: string[]): StageStatusValue {
  const currentIdx = STAGE_ORDER.indexOf(runStatus);
  const firstTarget = targetStages[0];
  const targetIdx = STAGE_ORDER.indexOf(firstTarget);
  if (targetStages.includes(runStatus)) return "active";
  if (currentIdx > targetIdx) return "completed";
  return "pending";
}

export function getDepthBudget(configSnapshot: Record<string, unknown>): number {
  const reasoning = configSnapshot?.reasoning as Record<string, number> | undefined;
  return reasoning?.depth_budget ?? 3;
}

export interface BudgetViewComputed {
  rag_queries_remaining: number;
  external_search_queries_remaining: number;
  total_cost_estimate: string;
}
