/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'accent': '#7c4dff',
        'accent-hover': '#6a3de8',
        'accent-alt': '#00b8d4',
        'up': '#69f0ae',
        'down': '#ff6e40',
        'warn': '#ffd740',
        'surface': '#0a0a0f',
        'surface-alt': '#13131a',
        'surface-elevated': '#1c1c28',
        'surface-overlay': '#222233',
        'surface-hover': '#2a2a3d',
        'line': '#222233',
        'line-light': '#2e2e44',
        'txt': '#ffffff',
        'txt-sec': '#d0d0e0',
        'txt-dim': '#9090a8',
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
