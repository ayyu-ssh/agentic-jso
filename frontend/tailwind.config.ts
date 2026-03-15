import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        panel: "var(--panel)",
        ink: "var(--ink)",
        accent: "var(--accent)",
        ember: "var(--ember)",
      },
      boxShadow: {
        soft: "0 10px 35px rgba(0,0,0,0.14)",
      },
      keyframes: {
        riseIn: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0px)" },
        },
      },
      animation: {
        riseIn: "riseIn 500ms ease-out forwards",
      },
    },
  },
  plugins: [],
};

export default config;
