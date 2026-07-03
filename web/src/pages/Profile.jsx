// Профиль «игрока»: уровень, XP, звание, витрина стат, heatmap за год,
// последние ачивки.
import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { fmtHdec } from '../util'
import { StatTile, ProgressBar } from '../components/bits'
import Heatmap from '../components/Heatmap'

export default function Profile() {
  const [p, setP] = useState(null)
  useEffect(() => { api.profile().then(setP).catch(() => {}) }, [])

  if (!p) return <div className="p-8 text-ink-dim text-sm">Загрузка...</div>
  const f = p.facts

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* ── Шапка профиля ── */}
      <div className="card overflow-hidden">
        <div className="h-24 relative"
          style={{ background: 'linear-gradient(100deg,#0f2942 0%,#173a5e 45%,#2b2a55 100%)' }}>
          <div className="absolute inset-0 opacity-[0.07]"
            style={{ backgroundImage: 'repeating-linear-gradient(0deg,#000 0 1px,transparent 1px 4px)' }} />
        </div>
        <div className="px-6 pb-5 -mt-10 relative flex items-end gap-5 flex-wrap">
          <div className="w-24 h-24 rounded-2xl grid place-items-center text-5xl bg-surf2 border-2 border-accent/60 shadow-glow">
            ⌚
          </div>
          <div className="flex-1 min-w-[220px] pb-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-black tracking-tight">Разработчик</h1>
              <span className="chip bg-accent/15 text-accent">{p.rank}</span>
            </div>
            <div className="flex items-center gap-3 mt-2">
              <span className="w-9 h-9 rounded-full grid place-items-center text-sm font-black text-bg shrink-0"
                style={{ background: 'linear-gradient(135deg,#4fc3f7,#7c4dff)' }}>
                {p.level}
              </span>
              <div className="flex-1 max-w-sm">
                <ProgressBar pct={p.level_pct} h={8} />
                <p className="text-[11px] text-ink-dim mt-1 font-mono">
                  {p.xp.toLocaleString('ru')} XP · до уровня {p.level + 1} ещё {p.xp_to_next.toLocaleString('ru')} XP
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Витрина стат ── */}
      <div className="flex gap-3 mt-5 flex-wrap">
        <StatTile label="Наиграно всего" value={fmtHdec(f.total_s)} accent="#4fc3f7" />
        <StatTile label="Сессий" value={f.sessions} />
        <StatTile label="Проектов" value={f.projects} sub={f.completed ? `${f.completed} завершено` : undefined} />
        <StatTile label="Активных дней" value={f.active_days} sub={f.first_day ? `с ${f.first_day}` : undefined} />
        <StatTile label="Streak" value={`${f.overall_streak}д ${f.overall_streak >= 3 ? '🔥' : ''}`}
          accent={f.overall_streak >= 3 ? '#ffab40' : undefined} />
      </div>

      {/* ── Heatmap ── */}
      <div className="card p-4 mt-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">Активность за год</span>
        </div>
        <Heatmap daily={p.heatmap} />
      </div>

      {/* ── Последние ачивки ── */}
      <div className="card p-4 mt-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">
            Ачивки · {p.achievements_unlocked}/{p.achievements_total}
          </span>
          <Link to="/achievements" className="text-[12px] text-accent hover:underline">Все ачивки →</Link>
        </div>
        {p.recent_achievements.length === 0 ? (
          <p className="text-sm text-ink-dim">Пока пусто — заверши первую сессию!</p>
        ) : (
          <div className="flex gap-3 flex-wrap">
            {p.recent_achievements.map((a) => (
              <div key={a.id} title={`${a.title} — ${a.desc}`}
                className="w-16 h-16 grid place-items-center text-3xl rounded-xl bg-surf2 border border-accent/40 shadow-glow">
                {a.icon}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
