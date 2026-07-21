/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Professional Trading Platform - Bloomberg/TradingView inspired
        'accent': '#2962FF',
        'accent-hover': '#1E4BD8',
        'accent-soft': 'rgba(41, 98, 255, 0.08)',
        'up': '#00C853',
        'up-soft': 'rgba(0, 200, 83, 0.08)',
        'down': '#FF1744',
        'down-soft': 'rgba(255, 23, 68, 0.08)',
        'warn': '#FF9100',
        'warn-soft': 'rgba(255, 145, 0, 0.08)',
        // Dark surfaces
        'bg': '#0D1117',
        'bg-alt': '#161B22',
        'bg-elevated': '#1C2128',
        'bg-overlay': '#21262D',
        'bg-hover': '#282E36',
        // Borders
        'line': '#30363D',
        'line-light': '#3D444D',
        // Text
        'txt': '#F0F6FC',
        'txt-sec': '#8B949E',
        'txt-dim': '#6E7681',
        'txt-inv': '#0D1117',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Noto Sans', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['SF Mono', 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'monospace'],
      },
      fontSize: {
        'xxs': ['0.6875rem', { lineHeight: '1rem' }],
      }
    },
  },
  plugins: [],
}
