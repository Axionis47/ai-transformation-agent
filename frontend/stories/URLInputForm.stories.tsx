import type { Meta, StoryObj } from "@storybook/react";
import URLInputForm from "@/components/URLInputForm";

const meta: Meta<typeof URLInputForm> = {
  title: "Components/URLInputForm",
  component: URLInputForm,
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj<typeof URLInputForm>;

export const Idle: Story = {
  args: {
    onSubmit: (url, dryRun) => console.log("submit", url, dryRun),
    isLoading: false,
  },
};

export const Loading: Story = {
  args: {
    onSubmit: () => {},
    isLoading: true,
  },
};
