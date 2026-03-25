import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#0A0A0F',
          raised: '#111118',
          overlay: '#1A1A24',
          inset: '#08080C',
        },
        edge: {
          subtle: '#1E1E2A',
          DEFAULT: '#2A2A3A',
          strong: '#3A3A4E',
        },
        ink: {
          DEFAULT: '#EEEEF0',
          secondary: '#9394A1',
          tertiary: '#55566A',
          inverse: '#0A0A0F',
        },
        mint: {
          DEFAULT: '#34D399',
          dim: '#059669',
          bright: '#6EE7B7',
        },
        amber: {
          DEFAULT: '#FBBF24',
          dim: '#D97706',
        },
        rose: {
          DEFAULT: '#FB7185',
          dim: '#E11D48',
        },
        indigo: {
          DEFAULT: '#818CF8',
          dim: '#6366F1',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['11px', '16px'],
        xs: ['12px', '18px'],
        sm: ['13px', '20px'],
        base: ['14px', '22px'],
        lg: ['16px', '24px'],
        xl: ['20px', '28px'],
        '2xl': ['28px', '36px'],
      },
      maxWidth: {
        prose: '72ch',
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

export default config
