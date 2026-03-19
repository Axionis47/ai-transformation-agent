import type { Meta, StoryObj } from "@storybook/react";
import UseCaseTierSection from "@/components/UseCaseTierSection";
import type { TieredUseCase } from "@/lib/types";

const meta: Meta<typeof UseCaseTierSection> = {
  title: "Components/UseCaseTierSection",
  component: UseCaseTierSection,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof UseCaseTierSection>;

const FLOW = {
  data_inputs: ["Historical data"],
  model_approach: "ML scoring",
  output_consumer: "Ops dashboard",
  feedback_loop: "Monthly",
  value_measurement: "Cost per unit",
};

const ALL_TIERS: TieredUseCase[] = [
  {
    tier: "LOW_HANGING_FRUIT",
    title: "Carrier Performance Scoring",
    description: "Score carriers on historical on-time and cost data.",
    evidence_signal_ids: ["sig-001"],
    effort: "Low",
    impact: "Medium",
    roi_estimate: "10-12% cost reduction",
    roi_basis: "Proven across similar logistics engagements",
    rag_benchmark: "14% fuel cost reduction over 4 months",
    confidence: 0.82,
    why_this_company: "You already have BigQuery with shipment history.",
    data_flow: FLOW,
    win_id: "win-002",
    proven_metric: "14% fuel cost reduction",
    client_profile_match: "mid-market LTL carrier, 520 employees, US Midwest",
  },
  {
    tier: "MEDIUM_SOLUTION",
    title: "Demand Forecasting",
    description: "Predict shipment volumes 4 weeks ahead.",
    evidence_signal_ids: [],
    effort: "Medium",
    impact: "High",
    roi_estimate: "12-16% capacity waste reduction",
    roi_basis: "Base win 20% discounted for cross-domain adaptation",
    rag_benchmark: null,
    confidence: 0.68,
    why_this_company: "2M monthly shipments give you the training data.",
    data_flow: FLOW,
    base_win_id: "win-005",
    adaptation_notes: "Base win was retail. Logistics adds lead-time variability — ~30% extra effort estimated.",
    adjusted_roi_range: "12-16% — discounted from 20% base",
  },
  {
    tier: "HARD_EXPERIMENT",
    title: "Autonomous Routing",
    description: "RL agent for real-time routing across 200+ carriers.",
    evidence_signal_ids: [],
    effort: "High",
    impact: "High",
    roi_estimate: "25-35% logistics cost reduction",
    roi_basis: "Industry estimate — no direct Tenex precedent",
    rag_benchmark: "Amazon Logistics 35% reduction (2022)",
    confidence: 0.41,
    why_this_company: "Network scale justifies the investment.",
    data_flow: FLOW,
    industry_examples: ["Amazon Logistics", "UPS ORION"],
    source_citations: ["McKinsey Logistics AI Report 2023", "Amazon press release 2022"],
  },
];

export const AllTiers: Story = { args: { useCases: ALL_TIERS } };

export const OnlyDelivered: Story = {
  args: { useCases: ALL_TIERS.filter((u) => u.tier === "LOW_HANGING_FRUIT") },
};

export const DeliveredAndAdaptation: Story = {
  args: { useCases: ALL_TIERS.filter((u) => u.tier !== "HARD_EXPERIMENT") },
};

export const OnlyAmbitious: Story = {
  args: { useCases: ALL_TIERS.filter((u) => u.tier === "HARD_EXPERIMENT") },
};

export const Empty: Story = { args: { useCases: [] } };
