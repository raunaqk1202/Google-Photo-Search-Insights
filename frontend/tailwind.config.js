/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"Roboto Mono"', 'monospace'],
      },
      colors: {
        google: {
          blue: '#1a73e8',
          blueHover: '#1557b0',
          blueLight: '#e8f0fe',
          blueSubtle: '#f1f5fe',
          red: '#ea4335',
          redLight: '#fce8e6',
          yellow: '#fbbc04',
          yellowLight: '#fef7e0',
          green: '#34a853',
          greenLight: '#e6f4ea',
          grayBg: '#f8fafd',
          graySurface: '#ffffff',
          grayBorder: '#dadce0',
          grayText: '#3c4043',
          grayMuted: '#5f6368',
          grayLight: '#f1f3f4',
        }
      },
      boxShadow: {
        'elevation-1': '0 1px 3px 1px rgba(60, 64, 67, 0.15), 0 1px 2px 0 rgba(60, 64, 67, 0.3)',
        'elevation-2': '0 2px 6px 2px rgba(60, 64, 67, 0.15), 0 1px 2px 0 rgba(60, 64, 67, 0.3)',
        'gemini-pill': '0 4px 16px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
}
