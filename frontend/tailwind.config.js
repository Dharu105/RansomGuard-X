/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#050914",
          panel: "#0B1220",
          raised: "#101927",
          border: "#1D2A3A",
          muted: "#7D8CA0",
          text: "#E8F0F8",
          accent: "#38BDF8",
          cyan: "#22D3EE",
          blue: "#3B82F6",
          purple: "#8B5CF6",
          good: "#22C55E",
          warn: "#F59E0B",
          high: "#F97316",
          crit: "#EF4444",
        },
      },
      fontFamily: {
        sans: ["Inter", "Geist", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      keyframes: {
        "event-in": {
          "0%": { opacity: "0", transform: "translateY(-4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
        "node-ring": {
          "0%, 100%": { boxShadow: "0 0 0 1px rgba(34,211,238,0.45)" },
          "50%": { boxShadow: "0 0 0 4px rgba(34,211,238,0.12)" },
        },
      },
      animation: {
        "event-in": "event-in 220ms ease-out",
        "pulse-dot": "pulse-dot 1.6s ease-in-out infinite",
        "node-ring": "node-ring 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
