/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#0b0d12',
        sidebar: '#0f1219',
        surf:    '#151a26',
        surf2:   '#1a2030',
        surf3:   '#1f263a',
        line:    '#242d42',
        accent:  '#4fc3f7',
        ok:      '#00e676',
        danger:  '#ff5252',
        warn:    '#ffab40',
        ink:     '#dde3f0',
        'ink-soft': '#9aa6c3',
        'ink-dim':  '#69779d',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'Cascadia Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        capsule: '0 8px 24px rgba(0,0,0,.45)',
        glow: '0 0 0 1px rgba(79,195,247,.35), 0 8px 32px rgba(79,195,247,.15)',
      },
    },
  },
  plugins: [],
}
