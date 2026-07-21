/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Professional Trading Platform Palette
        'accent': '#3B82F6',
        'accent-hover': '#2563EB',
        'up': '#22C55E',
        'up-muted': '#166534',
        'down': '#EF4444',
        'down-muted': '#991B1B',
        'surface': {
          0: '#0B0D11',
          1: '#111318',
          2: '#171A20',
          3: '#1E2128',
          4: '#252830',
          5: '#2C3038',
        },
        'border': {
          DEFAULT: '#2A2D35',
          light: '#353840',
        },
        'text': {
          primary: '#E8EAED',
          secondary: '#9CA3AF',
          muted: '#6B7280',
        }
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
