export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17324d",
        skywash: "#e0f2fe",
        seafoam: "#dcfce7",
        ambersoft: "#fef3c7",
        coralsoft: "#fee2e2",
      },
      fontFamily: {
        sans: ['"Avenir Next"', "ui-sans-serif", "system-ui"],
      },
      boxShadow: {
        calm: "0 20px 50px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

