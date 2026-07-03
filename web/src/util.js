// Форматирование и цветовые утилиты — зеркало utils.py.

export function fmtH(seconds) {
  const s = Math.floor(seconds || 0)
  if (s < 60) return `${s}с`
  if (s < 3600) return `${Math.floor(s / 60)}м`
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return m ? `${h}ч ${m}м` : `${h}ч`
}

export function fmtHdec(seconds) {
  return `${((seconds || 0) / 3600).toFixed(1)}ч`
}

export function fmtHMS(seconds) {
  const s = Math.floor(seconds || 0)
  const p = (n) => String(n).padStart(2, '0')
  return `${p(Math.floor(s / 3600))}:${p(Math.floor((s % 3600) / 60))}:${p(s % 60)}`
}

export function hexToRgb(hex) {
  const h = hex.replace('#', '')
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16))
}

const toHex = (r, g, b) =>
  '#' + [r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('')

export function darken(hex, f = 0.4) {
  const [r, g, b] = hexToRgb(hex)
  return toHex(r * (1 - f), g * (1 - f), b * (1 - f))
}

export function blend(fg, bg, a) {
  const [fr, fgc, fb] = hexToRgb(fg)
  const [br, bgc, bb] = hexToRgb(bg)
  return toHex(fr * a + br * (1 - a), fgc * a + bgc * (1 - a), fb * a + bb * (1 - a))
}

// Градиент капсулы/hero из акцентного цвета проекта
export function capsuleGradient(color) {
  return `linear-gradient(135deg, ${darken(color, 0.78)} 0%, ${darken(color, 0.5)} 55%, ${color} 130%)`
}

export function heroGradient(color) {
  return `linear-gradient(100deg, ${darken(color, 0.85)} 0%, ${darken(color, 0.6)} 45%, ${darken(color, 0.25)} 100%)`
}

export const EMOJIS = [
  '💻','🚀','🔬','⚡','🛠️','🧠','📊','🤖','🔐','🌐',
  '🎯','📱','🔧','🧪','💡','🏗️','📡','🎮','📈','🧩',
  '🔮','⚙️','🗄️','🧲','📝','🏆','🌿','🎲',
]

export const PROJECT_COLORS = [
  '#4fc3f7', '#7c4dff', '#00e676', '#ffab40', '#f06292',
  '#4db6ac', '#ff5252', '#aed581', '#ba68c8', '#ffd54f',
]

export const STATUS_META = {
  active:    { label: 'Активный',  cls: 'text-accent',  chip: 'bg-accent/15 text-accent' },
  completed: { label: 'Завершён',  cls: 'text-ok',      chip: 'bg-ok/15 text-ok' },
  deleted:   { label: 'Удалён',    cls: 'text-danger',  chip: 'bg-danger/15 text-danger' },
}

export function fmtDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-')
  return `${d}.${m}.${y}`
}
