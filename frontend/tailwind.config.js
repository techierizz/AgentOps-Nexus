/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bgDeep: "#0B0A0F",
        bgCard: "#13111C",
        bgHover: "#1E1A2D",
        accentPurple: "#8B5CF6",
        accentPurpleLight: "#A78BFA",
        accentGreen: "#10B981",
        accentGreenLight: "#34D399",
        accentRed: "#EF4444",
        borderDark: "#26213A",
        textMuted: "#9CA3AF"
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      }
    },
  },
  plugins: [],
}
