import type { Meta, StoryObj } from "@storybook/react";
import PipelineProgress from "@/components/PipelineProgress";

const meta: Meta<typeof PipelineProgress> = {
  title: "Components/PipelineProgress",
  component: PipelineProgress,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof PipelineProgress>;

export const Default: Story = {};
