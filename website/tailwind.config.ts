// Tailwind CSS v4 uses CSS-based configuration via @import "tailwindcss"
// See index.css for the new v4 syntax
// This file is kept for backwards compatibility but no longer used
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './App.tsx',
    './components/**/*.{ts,tsx}',
    './pages/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

export default config
