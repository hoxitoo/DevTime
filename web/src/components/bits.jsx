// Мелкие переиспользуемые элементы: стат-плитка, прогресс-бар, тосты.
import React from 'react'
import { useStore } from '../store'

export function StatTile({ label, value, accent, sub }) {
  return (
    <div className="card px-4 py-3 flex-1 min-w-[120px]">
      <p className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">{label}</p>
      <p className="text-2xl font-black mt-0.5" style={accent ? { color: accent } : undefined}>{value}</p>
      {sub && <p className="text-[11px] text-ink-dim mt-0.5">{sub}</p>}
    </div>
  )
}

export function ProgressBar({ pct, color = '#4fc3f7', h = 10 }) {
  return (
    <div className="w-full rounded-full bg-surf2 overflow-hidden" style={{ height: h }}>
      <div className="h-full rounded-full transition-[width] duration-500"
        style={{ width: `${Math.min(100, pct)}%`, background: `linear-gradient(90deg, ${color}aa, ${color})` }} />
    </div>
  )
}

export function Toasts() {
  const { toasts } = useStore()
  return (
    <div className="fixed bottom-5 right-5 z-50 space-y-2 w-80">
      {toasts.map((t) => (
        <div key={t.id}
          className={`toast-enter glass rounded-xl px-4 py-3 flex items-center gap-3 shadow-capsule ${
            t.glow ? '!border-accent/60 shadow-glow' : ''}`}>
          <span className="text-2xl">{t.icon}</span>
          <div className="min-w-0">
            <p className={`text-[11px] font-bold uppercase tracking-wider ${t.glow ? 'text-accent' : 'text-ink-dim'}`}>{t.title}</p>
            <p className="text-sm font-semibold truncate">{t.text}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
