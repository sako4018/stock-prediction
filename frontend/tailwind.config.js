/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Accent
        'accent': '#2962FF',
        'accent-hover': '#1E4BD8',
        'up': '#00C853',
        'down': '#FF1744',
        'warn': '#FF9100',
        // Surfaces — prefixed 'surface-' so bg-surface-* generates correctly
        'surface': '#0D1117',
        'surface-alt': '#161B22',
        'surface-elevated': '#1C2128',
        'surface-overlay': '#21262D',
        'surface-hover': '#282E36',
        // Borders
        'line': '#30363D',
        'line-light': '#3D444D',
        // Text
        'txt': '#F0F6FC',
        'txt-sec': '#8B949E',
        'txt-dim': '#6E7681',
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
