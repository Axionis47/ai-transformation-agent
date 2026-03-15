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
    id: "win-001",
    engagement_title: "Logistics AI Maturity Uplift",
    industry: "Logistics",
    size_label: "Mid-market",
    primary_metric_label: "Fulfillment accuracy",
    primary_metric_value: "+18%",
    measurement_period: "6 months post-deployment",
    maturity_at_engagement: "Developing",
  },
  {
    id: "win-042",
    engagement_title: "Retail Demand Forecasting",
    industry: "Retail",
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
    wins: [{ id: "win-099", engagement_title: "Healthcare AI Pilot", industry: "Healthcare" }],
  },
};

export const Empty: Story = {
  args: { wins: [] },
};
