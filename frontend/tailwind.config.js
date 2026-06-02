/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        telecom: {
          blue: '#1e40af',
          dark: '#0f172a',
          accent: '#3b82f6',
        },
      },
    },
  },
  plugins: [],
}
