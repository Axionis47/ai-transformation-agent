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
          bg: "#e8ecf1",
          dark: "#bec8d4",
          light: "#ffffff",
        },
        accent: {
          DEFAULT: "#4f6df5",
          hover: "#3b5de7",
        },
      },
      boxShadow: {
        "neo-raised": "5px 5px 10px #bec8d4, -5px -5px 10px #ffffff",
        "neo-flat": "2px 2px 5px #bec8d4, -2px -2px 5px #ffffff",
        "neo-inset": "inset 2px 2px 5px #bec8d4, inset -2px -2px 5px #ffffff",
        "neo-btn": "3px 3px 7px #bec8d4, -3px -3px 7px #ffffff",
        "neo-btn-pressed": "inset 2px 2px 4px #bec8d4, inset -2px -2px 4px #ffffff",
      },
      borderRadius: {
        neo: "12px",
        "neo-sm": "8px",
        "neo-lg": "20px",
      },
    },
  },
  plugins: [],
};

export default config;
