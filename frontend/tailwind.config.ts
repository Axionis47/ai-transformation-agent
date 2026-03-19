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
        cream: "#f5f0e8",
        ink: "#1a1714",
        "ink-medium": "#3d3830",
        "ink-light": "#8a8279",
        "ink-faint": "#b8b0a4",
        rule: "#c9c1b4",
        red: "#c1272d",
        "red-light": "rgba(193,39,45,0.08)",
      },
      fontFamily: {
        headline: ["Playfair Display", "Georgia", "serif"],
        body: ["Libre Baskerville", "Georgia", "serif"],
        mono: ["IBM Plex Mono", "Menlo", "monospace"],
        label: ["Barlow Condensed", "Arial Narrow", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
