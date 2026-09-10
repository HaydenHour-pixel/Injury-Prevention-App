/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark-only UI (no light mode toggle in this slice). Named tokens
        // rather than raw Tailwind grays so intent stays visible at call
        // sites: "surface" is a card, "ink" is body text.
        //
        // Named "canvas", not "base": Tailwind's default theme already has a
        // fontSize scale entry called "base" (the 1rem size), and both live
        // under the shared "text-" prefix. A color also named "base" collides
        // with it there — `text-base` silently became this color instead of
        // font-size 1rem everywhere it was used for sizing.
        canvas: "#0a0a0a",
        surface: "#141414",
        border: "#2a2a2a",
        ink: "#f2f2f2",
        muted: "#9a9a9a",
        accent: "#f97316",
        "accent-ink": "#0a0a0a",
        danger: "#f87171",
        good: "#4ade80",
      },
    },
  },
  plugins: [],
};
