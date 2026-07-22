/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'accent': 'rgb(var(--color-accent) / <alpha-value>)',
        'accent-hover': 'rgb(var(--color-accent-hover) / <alpha-value>)',
        'accent-alt': 'rgb(var(--color-accent-alt) / <alpha-value>)',
        'accent-blue': 'rgb(var(--color-accent-blue) / <alpha-value>)',
        'up': 'rgb(var(--color-up) / <alpha-value>)',
        'down': 'rgb(var(--color-down) / <alpha-value>)',
        'warn': 'rgb(var(--color-warn) / <alpha-value>)',
        'surface': 'rgb(var(--color-surface) / <alpha-value>)',
        'surface-alt': 'rgb(var(--color-surface-alt) / <alpha-value>)',
        'surface-elevated': 'rgb(var(--color-surface-elevated) / <alpha-value>)',
        'surface-overlay': 'rgb(var(--color-surface-overlay) / <alpha-value>)',
        'surface-hover': 'rgb(var(--color-surface-hover) / <alpha-value>)',
        'line': 'rgb(var(--color-line) / <alpha-value>)',
        'line-light': 'rgb(var(--color-line-light) / <alpha-value>)',
        'txt': 'rgb(var(--color-txt) / <alpha-value>)',
        'txt-sec': 'rgb(var(--color-txt-sec) / <alpha-value>)',
        'txt-dim': 'rgb(var(--color-txt-dim) / <alpha-value>)',
        'txt-muted': 'rgb(var(--color-txt-muted) / <alpha-value>)',
        'frame': 'rgb(var(--color-frame) / <alpha-value>)',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        sans: ['"DM Sans"', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'SF Mono', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      fontSize: {
        'xxs': ['0.6875rem', { lineHeight: '1rem' }],
      },
      animation: {
        'grain': 'grain 8s steps(10) infinite',
      },
      keyframes: {
        grain: {
          '0%, 100%': { transform: 'translate(0, 0)' },
          '10%': { transform: 'translate(-5%, -10%)' },
          '20%': { transform: 'translate(-15%, 5%)' },
          '30%': { transform: 'translate(7%, -25%)' },
          '40%': { transform: 'translate(-5%, 25%)' },
          '50%': { transform: 'translate(-15%, 10%)' },
          '60%': { transform: 'translate(15%, 0%)' },
          '70%': { transform: 'translate(0%, 15%)' },
          '80%': { transform: 'translate(3%, 35%)' },
          '90%': { transform: 'translate(-10%, 10%)' },
        },
      },
    },
  },
  plugins: [],
}
