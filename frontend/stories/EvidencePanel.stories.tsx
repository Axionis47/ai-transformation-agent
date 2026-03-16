import type { Meta, StoryObj } from "@storybook/react";
import EvidencePanel from "@/components/EvidencePanel";
import type { VictoryMatch } from "@/lib/types";

const meta: Meta<typeof EvidencePanel> = {
  title: "Components/EvidencePanel",
  component: EvidencePanel,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof EvidencePanel>;

const SAMPLE_WINS: VictoryMatch[] = [
  {
    win_id: "win-001",
    engagement_title: "Logistics AI Maturity Uplift",
    industry: "Logistics",
    match_tier: "DIRECT_MATCH",
    roi_benchmark: "18%",
    confidence: 0.88,
    size_label: "Mid-market",
    primary_metric_label: "Fulfillment accuracy",
    primary_metric_value: "+18%",
    measurement_period: "6 months post-deployment",
    maturity_at_engagement: "Developing",
  },
  {
    win_id: "win-042",
    engagement_title: "Retail Demand Forecasting",
    industry: "Retail",
    match_tier: "CALIBRATION_MATCH",
    roi_benchmark: "23%",
    confidence: 0.72,
    size_label: "Enterprise",
    primary_metric_label: "Inventory waste reduction",
    primary_metric_value: "23%",
    measurement_period: "Q3 2024",
    maturity_at_engagement: "Emerging",
  },
];

export const WithWins: Story = {
  args: { wins: SAMPLE_WINS },
};

export const SingleWin: Story = {
  args: {
    wins: [SAMPLE_WINS[0]],
  },
};

export const MinimalData: Story = {
  args: {
    wins: [
      {
        win_id: "win-099",
        engagement_title: "Healthcare AI Pilot",
        industry: "Healthcare",
        match_tier: "ADJACENT_MATCH",
        roi_benchmark: "8%",
        confidence: 0.6,
      },
    ],
  },
};

export const Empty: Story = {
  args: { wins: [] },
};
