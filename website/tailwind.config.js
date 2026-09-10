/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'studio-bg': '#E4E4E4',
        'studio-cream': '#F4F1E8',
        'studio-accent': '#75C5DE',
        'studio-ink': '#111111',
        'studio-ink-dark': '#0B0B0B',
        'studio-muted': '#9A9590',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
