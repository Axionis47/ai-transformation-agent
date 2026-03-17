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
          bg: "#edf0f5",
          dark: "#c4cad6",
          light: "#ffffff",
        },
        accent: {
          DEFAULT: "#4f6df5",
          hover: "#3b5de7",
          active: "#2f4fd4",
        },
        slate: {
          750: "#2d3748",
          850: "#1a202c",
        },
      },
      textColor: {
        heading: "#1e2433",
        body: "#4a5568",
        muted: "#718096",
        accent: "#4f6df5",
      },
      boxShadow: {
        "neo-raised": "6px 6px 14px #c4cad6, -6px -6px 14px #ffffff",
        "neo-flat": "3px 3px 8px #c4cad6, -3px -3px 8px #ffffff",
        "neo-inset": "inset 3px 3px 7px #c4cad6, inset -3px -3px 7px #ffffff",
        "neo-btn": "4px 4px 10px #c4cad6, -4px -4px 10px #ffffff",
        "neo-btn-pressed": "inset 2px 2px 6px rgba(0,0,0,0.15), inset -2px -2px 4px rgba(255,255,255,0.6)",
        "accent-btn": "4px 4px 12px rgba(79, 109, 245, 0.4), -2px -2px 8px rgba(255,255,255,0.8)",
        "accent-btn-hover": "5px 5px 16px rgba(79, 109, 245, 0.5), -2px -2px 8px rgba(255,255,255,0.9)",
        "focus-ring": "0 0 0 3px rgba(79, 109, 245, 0.35)",
      },
      borderRadius: {
        neo: "16px",
        "neo-sm": "10px",
        "neo-lg": "24px",
      },
      backgroundImage: {
        "neo-gradient": "linear-gradient(135deg, #edf0f5 0%, #e8ecf2 60%, #eaecf5 100%)",
        "accent-gradient": "linear-gradient(135deg, #5a76f6 0%, #4f6df5 50%, #4463ef 100%)",
        "accent-gradient-hover": "linear-gradient(135deg, #4f6df5 0%, #3b5de7 50%, #3050d8 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
