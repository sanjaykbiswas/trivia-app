/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          main: '#3f51b5',
          light: '#757de8',
          dark: '#002984',
          contrastText: '#ffffff',
        },
        secondary: {
          main: '#f50057',
          light: '#ff5983',
          dark: '#bb002f',
          contrastText: '#ffffff',
        },
        background: {
          default: '#f5f5f5',
          light: '#ffffff',
          dark: '#e0e0e0',
        },
        text: {
          primary: '#212121',
          secondary: '#757575',
          disabled: '#9e9e9e',
        },
        error: {
          main: '#f44336',
          light: '#ff7961',
          dark: '#ba000d',
        },
        success: {
          main: '#4caf50',
          light: '#80e27e',
          dark: '#087f23',
        },
      },
      animation: {
        'slide-up': 'slide-up 0.3s ease-out forwards',
        'scale-in': 'scale-in 0.3s ease-out forwards',
      },
      keyframes: {
        'slide-up': {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.9)', opacity: 0 },
          '100%': { transform: 'scale(1)', opacity: 1 },
        },
      },
    },
  },
  plugins: [],
};