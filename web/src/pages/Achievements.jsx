// Витрина ачивок: полученные светятся, остальные показывают прогресс.
import React, { useEffect, useState } from 'react'
import { api } from '../api'
import { fmtH } from '../util'
import { ProgressBar } from '../components/bits'

export default function Achievements() {
  const [items, setItems] = useState(null)
  useEffect(() => { api.achievements().then(setItems).catch(() => {}) }, [])

  if (!items) return <div className="p-8 text-ink-dim text-sm">Загрузка...</div>
  const unlocked = items.filter((a) => a.unlocked).length

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-end justify-between mb-2 flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Ачивки</h1>
          <p className="text-sm text-ink-dim mt-1">Каждый час за кодом приближает следующую.</p>
        </div>
        <span className="text-sm font-bold text-accent font-mono">{unlocked} / {items.length}</span>
      </div>
      <ProgressBar pct={(unlocked / items.length) * 100} h={8} />

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-6">
        {items.map((a) => (
          <div key={a.id}
            className={`card p-4 flex gap-3.5 items-start transition-colors ${
              a.unlocked ? '!border-accent/50 shadow-glow' : ''}`}>
            <span className={`text-4xl leading-none ${a.unlocked ? 'drop-shadow-[0_0_10px_rgba(79,195,247,.5)]' : 'grayscale opacity-40'}`}>
              {a.icon}
            </span>
            <div className="flex-1 min-w-0">
              <p className={`font-bold text-[14px] ${a.unlocked ? '' : 'text-ink-soft'}`}>{a.title}</p>
              <p className="text-[12px] text-ink-dim mt-0.5 leading-4">{a.desc}</p>
              {a.unlocked ? (
                <p className="chip bg-accent/15 text-accent mt-2">Получено ✓</p>
              ) : (
                <div className="mt-2.5">
                  <ProgressBar pct={a.pct} h={6} color="#5d6a8a" />
                  <p className="text-[11px] text-ink-dim mt-1 font-mono">
                    {a.time_based ? `${fmtH(a.value)} / ${fmtH(a.target)}` : `${a.value} / ${a.target}`}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
