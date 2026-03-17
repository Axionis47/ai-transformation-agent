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
    relevance_note: "Near-identical tech stack and operational scale.",
    roi_benchmark: "18% fulfillment accuracy improvement in 6 months",
    similarity_score: 0.91,
    confidence: 0.88,
    gap_analysis: "Client lacked real-time warehouse telemetry at engagement start.",
  },
  {
    win_id: "win-042",
    engagement_title: "Retail Demand Forecasting",
    industry: "Retail",
    match_tier: "CALIBRATION_MATCH",
    relevance_note: "Strong data infrastructure match; different end market.",
    roi_benchmark: "23% inventory waste reduction over Q3 2024",
    similarity_score: 0.74,
    confidence: 0.72,
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
        relevance_note: "Similar organizational maturity, different domain.",
        roi_benchmark: "8% cost reduction in care coordination",
        similarity_score: 0.61,
        confidence: 0.6,
      },
    ],
  },
};

export const Empty: Story = {
  args: { wins: [] },
};
