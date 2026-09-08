/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sentinel: {
          900: '#0b0f19',
          850: '#111827',
          800: '#1e293b',
          700: '#334155',
          600: '#475569',
          500: '#64748b',
          accent: '#0284c7',
          alert: '#ef4444',
          warning: '#f59e0b',
          success: '#10b981',
        },
      },
    },
  },
  plugins: [],
}
