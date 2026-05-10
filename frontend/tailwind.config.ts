import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
      animation: {
        "lung-inhale": "lungInhale 4s ease-in-out infinite",
        "lung-inhale-right": "lungInhale 4s ease-in-out 0.5s infinite",
        "card-enter": "cardEnter 0.6s ease-out forwards",
      },
    },
  },
  plugins: [],
};
export default config;
