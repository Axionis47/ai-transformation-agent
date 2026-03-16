import type { Meta, StoryObj } from "@storybook/react";
import UseCaseCard from "@/components/UseCaseCard";
import type { TieredUseCase } from "@/lib/types";

const meta: Meta<typeof UseCaseCard> = {
  title: "Components/UseCaseCard",
  component: UseCaseCard,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof UseCaseCard>;

const DATA_FLOW = {
  data_inputs: ["Shipment history", "Carrier rate cards"],
  model_approach: "Weighted scoring model",
  output_consumer: "Operations team via dashboard",
  feedback_loop: "Monthly model refresh",
  value_measurement: "Per-shipment cost tracked monthly",
};

const LOW: TieredUseCase = {
  tier: "LOW_HANGING_FRUIT",
  title: "Carrier Performance Scoring",
  description: "Automate carrier scoring using historical on-time and cost data to guide routing decisions.",
  evidence_signal_ids: ["sig-001", "sig-002"],
  effort: "Low",
  impact: "Medium",
  roi_estimate: "10-12% reduction in carrier costs",
  roi_basis: "Based on win-002 at similar logistics SaaS company",
  rag_benchmark: "Mednax 12% cost reduction, 6-month payback",
  confidence: 0.82,
  why_this_company: "You already track shipment history in BigQuery — this needs no new data collection.",
  data_flow: DATA_FLOW,
};

const MEDIUM: TieredUseCase = {
  tier: "MEDIUM_SOLUTION",
  title: "Demand Forecasting Engine",
  description: "ML model predicting shipment volumes 4 weeks out to improve capacity planning.",
  evidence_signal_ids: ["sig-003"],
  effort: "Medium",
  impact: "High",
  roi_estimate: "15-20% reduction in capacity waste",
  roi_basis: "Based on retail demand forecasting benchmarks",
  rag_benchmark: null,
  confidence: 0.68,
  why_this_company: "Your 2M monthly shipments provide the training data volume required for reliable forecasting.",
  data_flow: DATA_FLOW,
};

const HARD: TieredUseCase = {
  tier: "HARD_EXPERIMENT",
  title: "Autonomous Route Optimization",
  description: "RL agent optimizing real-time routing decisions across 200+ carrier network.",
  evidence_signal_ids: [],
  effort: "High",
  impact: "High",
  roi_estimate: "25-35% logistics cost reduction",
  roi_basis: "Theoretical — no direct benchmark available",
  rag_benchmark: null,
  confidence: 0.41,
  why_this_company: "You have the network complexity and volume to justify the model training investment.",
  data_flow: DATA_FLOW,
};

export const LowHangingFruit: Story = { args: { useCase: LOW } };
export const MediumSolution: Story = { args: { useCase: MEDIUM } };
export const HardExperiment: Story = { args: { useCase: HARD } };
