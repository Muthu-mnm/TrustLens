/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#1e40af', light: '#3b82f6', dark: '#1e3a8a' },
        danger: { DEFAULT: '#dc2626', light: '#ef4444' },
        warning: { DEFAULT: '#d97706', light: '#f59e0b' },
        success: { DEFAULT: '#059669', light: '#10b981' },
        surface: { DEFAULT: '#f8fafc', card: '#ffffff', dark: '#0f172a' },
      }
    }
  },
  plugins: []
}
