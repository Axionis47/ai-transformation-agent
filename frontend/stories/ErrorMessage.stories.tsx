import type { Meta, StoryObj } from "@storybook/react";
import ErrorMessage from "@/components/ErrorMessage";

const meta: Meta<typeof ErrorMessage> = {
  title: "Components/ErrorMessage",
  component: ErrorMessage,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof ErrorMessage>;

export const ScrapeFailure: Story = {
  args: {
    message: "Could not reach that website. Try a different URL.",
    onReset: () => console.log("reset"),
  },
};

export const ServerDown: Story = {
  args: {
    message: "Could not reach the analysis server. Is it running?",
    onReset: () => console.log("reset"),
  },
};
