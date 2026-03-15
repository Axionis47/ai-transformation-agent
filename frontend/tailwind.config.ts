import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./stories/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        neo: {
          bg: "#e0e5ec",
          dark: "#a3b1c6",
          light: "#ffffff",
        },
      },
      boxShadow: {
        "neo-raised": "6px 6px 12px #a3b1c6, -6px -6px 12px #ffffff",
        "neo-flat": "3px 3px 6px #a3b1c6, -3px -3px 6px #ffffff",
        "neo-inset": "inset 6px 6px 12px #a3b1c6, inset -6px -6px 12px #ffffff",
      },
      borderRadius: {
        neo: "16px",
        "neo-sm": "8px",
        "neo-lg": "24px",
      },
    },
  },
  plugins: [],
};

export default config;
