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
  roi_basis: "Proven across similar logistics engagements",
  rag_benchmark: "14% fuel cost reduction over 4 months post-deployment",
  confidence: 0.82,
  why_this_company: "You already track shipment history in BigQuery — this needs no new data collection.",
  data_flow: DATA_FLOW,
  win_id: "win-002",
  proven_metric: "14% fuel cost reduction",
  client_profile_match: "mid-market logistics SaaS, 520 employees, US Midwest",
};

const MEDIUM: TieredUseCase = {
  tier: "MEDIUM_SOLUTION",
  title: "Demand Forecasting Engine",
  description: "ML model predicting shipment volumes 4 weeks out to improve capacity planning.",
  evidence_signal_ids: ["sig-003"],
  effort: "Medium",
  impact: "High",
  roi_estimate: "12-16% reduction in capacity waste",
  roi_basis: "Base win: 20% reduction. Adapted estimate with industry gap discount.",
  rag_benchmark: null,
  confidence: 0.68,
  why_this_company: "Your 2M monthly shipments provide the training data volume required for reliable forecasting.",
  data_flow: DATA_FLOW,
  base_win_id: "win-005",
  adaptation_notes: "Base win was retail sector. Logistics domain adds lead-time variability — adjusted model complexity upward by ~30% effort.",
  adjusted_roi_range: "12-16% — base win 20% discounted for cross-domain adaptation",
};

const HARD: TieredUseCase = {
  tier: "HARD_EXPERIMENT",
  title: "Autonomous Route Optimization",
  description: "RL agent optimizing real-time routing decisions across 200+ carrier network.",
  evidence_signal_ids: [],
  effort: "High",
  impact: "High",
  roi_estimate: "25-35% logistics cost reduction",
  roi_basis: "Industry estimate range — no direct Tenex precedent",
  rag_benchmark: "Amazon Logistics: 35% delivery cost reduction (2022)",
  confidence: 0.41,
  why_this_company: "You have the network complexity and volume to justify the model training investment.",
  data_flow: DATA_FLOW,
  industry_examples: ["Amazon Logistics", "UPS ORION", "FedEx SenseAware"],
  source_citations: ["McKinsey Logistics AI Report 2023", "Amazon press release 2022"],
};

export const LowHangingFruit: Story = { args: { useCase: LOW } };
export const MediumSolution: Story = { args: { useCase: MEDIUM } };
export const HardExperiment: Story = { args: { useCase: HARD } };

export const DeliveredNoOptionalFields: Story = {
  args: {
    useCase: {
      ...LOW,
      win_id: undefined,
      proven_metric: undefined,
      client_profile_match: undefined,
      rag_benchmark: null,
    },
  },
};
