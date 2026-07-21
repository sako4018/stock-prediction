/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'accent': '#3B82F6',
        'accent-hover': '#2563EB',
        'up': '#22C55E',
        'down': '#EF4444',
        'surface-0': '#0B0D11',
        'surface-1': '#111318',
        'surface-2': '#171A20',
        'surface-3': '#1E2128',
        'surface-4': '#252830',
        'surface-5': '#2C3038',
        'frame': '#2A2D35',
        'frame-light': '#353840',
        'label': '#E8EAED',
        'label-dim': '#9CA3AF',
        'label-muted': '#6B7280',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'xxs': ['0.65rem', { lineHeight: '0.875rem' }],
      }
    },
  },
  plugins: [],
}
