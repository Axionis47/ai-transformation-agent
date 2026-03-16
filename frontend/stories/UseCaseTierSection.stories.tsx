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
    effort: "Low", impact: "Medium",
    roi_estimate: "10-12% cost reduction",
    roi_basis: "Based on win-002",
    rag_benchmark: "Mednax 12% reduction",
    confidence: 0.82,
    why_this_company: "You already have BigQuery with shipment history.",
    data_flow: FLOW,
  },
  {
    tier: "MEDIUM_SOLUTION",
    title: "Demand Forecasting",
    description: "Predict shipment volumes 4 weeks ahead.",
    evidence_signal_ids: [],
    effort: "Medium", impact: "High",
    roi_estimate: "15-20% capacity waste reduction",
    roi_basis: "Industry benchmark",
    rag_benchmark: null,
    confidence: 0.68,
    why_this_company: "2M monthly shipments give you the training data.",
    data_flow: FLOW,
  },
  {
    tier: "HARD_EXPERIMENT",
    title: "Autonomous Routing",
    description: "RL agent for real-time routing across 200+ carriers.",
    evidence_signal_ids: [],
    effort: "High", impact: "High",
    roi_estimate: "25-35% logistics cost reduction",
    roi_basis: "Theoretical",
    rag_benchmark: null,
    confidence: 0.41,
    why_this_company: "Network scale justifies the investment.",
    data_flow: FLOW,
  },
];

export const AllTiers: Story = { args: { useCases: ALL_TIERS } };
export const OnlyLow: Story = { args: { useCases: ALL_TIERS.filter((u) => u.tier === "LOW_HANGING_FRUIT") } };
export const NoHard: Story = { args: { useCases: ALL_TIERS.filter((u) => u.tier !== "HARD_EXPERIMENT") } };
export const Empty: Story = { args: { useCases: [] } };
