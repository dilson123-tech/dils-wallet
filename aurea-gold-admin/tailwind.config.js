/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          50:"#fffdf5",100:"#fff9e6",200:"#ffedb3",300:"#ffe27f",
          400:"#ffd54f",500:"#ffb300",600:"#ff8f00",700:"#ff6f00",
          800:"#e65100",900:"#b34700"
        },
        carbon: { 900:"#0d0d0d",800:"#1a1a1a",700:"#262626",600:"#333333",500:"#404040" }
      }
    }
  },
  plugins: []
};
