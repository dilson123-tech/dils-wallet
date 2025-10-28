/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  safelist: [
    "bg-[#0a0a0a]",
    "bg-[#1a1a1a]",
    "bg-[#101010]",
    "bg-[#0f0f0f]",
    "bg-[#d4af37]",
    "text-[#d4af37]",
    "border-[#d4af37]",
    "shadow-[0_0_30px_rgba(212,175,55,0.15)]",
    "shadow-[0_0_40px_rgba(0,0,0,0.8)]",
    "shadow-[0_0_120px_rgba(212,175,55,0.3)_inset]",
    "hover:brightness-110",
    "active:scale-[0.98]",
    "rounded-2xl",
    "rounded-xl",
    "grid",
    "grid-cols-1",
    "md:grid-cols-3",
    "gap-6"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
