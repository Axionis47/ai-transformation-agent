import type { Meta, StoryObj } from "@storybook/react";
import ReportCard from "@/components/ReportCard";
import type { VictoryMatch } from "@/lib/types";

const meta: Meta<typeof ReportCard> = {
  title: "Components/ReportCard",
  component: ReportCard,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof ReportCard>;

const SAMPLE_CONTENT =
  "CargoLogik operates at a **Developing** stage of AI maturity (2.3/5).\n\n" +
  "The company processes over 2 million shipments monthly across 200+ logistics customers.\n\n" +
  "Their investment in a BigQuery data lake demonstrates data engineering maturity.";

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
];

export const ExecSummary: Story = {
  args: {
    title: "Executive Summary",
    content: SAMPLE_CONTENT,
  },
};

export const WithEvidencePanel: Story = {
  args: {
    title: "Executive Summary",
    content: SAMPLE_CONTENT,
    wins: SAMPLE_WINS,
  },
};

export const ShortContent: Story = {
  args: {
    title: "Current State",
    content: "Single paragraph with **bold text** and no double-newlines.",
  },
};

export const LongContent: Story = {
  args: {
    title: "ROI Analysis",
    content: Array(5).fill(SAMPLE_CONTENT).join("\n\n"),
  },
};
