/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html","./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Quicksand", "Inter", "sans-serif"]
      },
      colors: {
        pastel: {
          pink: "#FFB6C1",
          lavender: "#E9D5FF",
          sky: "#D7F9FF",
          mint: "#C6F6E9",
          peach: "#FFDCC0"
        }
      },
      backgroundImage: {
        "soft-gradient": "linear-gradient(135deg,#FFDCC0 0%, #E9D5FF 50%, #D7F9FF 100%)"
      }
    }
  },
  plugins: []
}
