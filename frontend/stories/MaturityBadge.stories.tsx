import type { Meta, StoryObj } from "@storybook/react";
import MaturityBadge from "@/components/MaturityBadge";

const meta: Meta<typeof MaturityBadge> = {
  title: "Components/MaturityBadge",
  component: MaturityBadge,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof MaturityBadge>;

export const WithScore: Story = {
  args: {
    score: 2.3,
    label: "Developing",
    elapsedSeconds: 47.3,
    costUsd: 0.011,
  },
};

export const HighScore: Story = {
  args: {
    score: 4.2,
    label: "Advanced",
    elapsedSeconds: 62.1,
    costUsd: 0.011,
  },
};

export const LowScore: Story = {
  args: {
    score: 1.1,
    label: "Beginner",
    elapsedSeconds: 38.5,
    costUsd: 0.009,
  },
};

export const NoScore: Story = {
  args: {
    elapsedSeconds: 51.2,
    costUsd: 0.011,
  },
};

export const NoMetadata: Story = {
  args: {},
};
