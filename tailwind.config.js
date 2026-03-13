/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./pages/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        pine: {
          50:  '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        },
        leaf: {
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        dark: {
          DEFAULT: '#0f0e0a',
          1:       '#1a1810',
          2:       '#252218',
          3:       '#302d1f',
        },
        cream: {
          DEFAULT: '#fdfcf8',
          1:       '#f5f2eb',
          2:       '#ede9e0',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
