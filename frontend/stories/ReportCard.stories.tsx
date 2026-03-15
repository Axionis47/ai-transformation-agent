import type { Meta, StoryObj } from "@storybook/react";
import ReportCard from "@/components/ReportCard";

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

export const ExecSummary: Story = {
  args: {
    title: "Executive Summary",
    content: SAMPLE_CONTENT,
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
