/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        darkBg: '#0b0f19',
        darkCard: '#111827',
        darkInput: '#1f2937',
        darkBorder: '#374151',
        brandGreen: '#16a34a',
        brandGreenHover: '#15803d',
      },
    },
  },
  plugins: [],
};
