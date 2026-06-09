/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0f0f1a',
        'bg-secondary': '#1a1a2e',
        'bg-card': '#16213e',
        'accent-gold': '#fbbf24',
        'accent-red': '#ef4444',
        'accent-blue': '#3b82f6',
        'accent-purple': '#a855f7',
        'accent-green': '#22c55e',
        'accent-orange': '#f97316',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease',
        'pulse-gold': 'pulseGold 1s ease-in-out infinite',
        'wolf-pulse': 'wolfPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGold: {
          '0%, 100%': { transform: 'scale(1)', boxShadow: '0 0 20px rgba(251, 191, 36, 0.5)' },
          '50%': { transform: 'scale(1.05)', boxShadow: '0 0 30px rgba(251, 191, 36, 0.8)' },
        },
        wolfPulse: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.1)' },
        },
      },
    },
  },
  plugins: [],
}
