import type { Preview } from "@storybook/react";
import "../app/globals.css";

const preview: Preview = {
  parameters: {
    backgrounds: {
      default: "neo",
      values: [{ name: "neo", value: "#e0e5ec" }],
    },
  },
};

export default preview;
