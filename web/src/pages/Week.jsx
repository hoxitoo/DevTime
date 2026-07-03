// Итоги недели: эта vs прошлая, по дням, топ проектов.
import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { api } from '../api'
import { fmtH, fmtHdec } from '../util'
import { StatTile, ProgressBar } from '../components/bits'

const DOW = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

export default function Week() {
  const [ins, setIns] = useState(null)
  const nav = useNavigate()
  useEffect(() => { api.weekInsights().then(setIns).catch(() => {}) }, [])

  const days = useMemo(() => {
    if (!ins) return []
    const map = Object.fromEntries(ins.daily.map((r) => [r.day, r.total]))
    const start = new Date(ins.week_start + 'T00:00:00')
    const out = []
    for (let i = 0; i < 7; i++) {
      const cur = new Date(start); cur.setDate(cur.getDate() + i)
      const prev = new Date(start); prev.setDate(prev.getDate() + i - 7)
      const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      out.push({
        label: DOW[i],
        cur: map[iso(cur)] || 0,
        prev: map[iso(prev)] || 0,
        isToday: iso(cur) === iso(new Date()),
        future: cur > new Date(),
      })
    }
    return out
  }, [ins])

  if (!ins) return <div className="p-8 text-ink-dim text-sm">Загрузка...</div>

  const delta = ins.previous_s ? Math.round((ins.current_s - ins.previous_s) / ins.previous_s * 100) : null
  const DeltaIcon = delta == null || delta === 0 ? Minus : delta > 0 ? TrendingUp : TrendingDown
  const deltaColor = delta == null || delta === 0 ? '#69779d' : delta > 0 ? '#00e676' : '#ff5252'
  const mx = Math.max(1, ...days.flatMap((d) => [d.cur, d.prev]))
  const topMax = Math.max(1, ...ins.top_projects.map((t) => t.total))

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-black tracking-tight">Итоги недели</h1>
      <p className="text-sm text-ink-dim mt-1">Неделя с {ins.week_start} против предыдущей.</p>

      <div className="flex gap-3 mt-5 flex-wrap">
        <StatTile label="Эта неделя" value={fmtHdec(ins.current_s)} accent="#4fc3f7" />
        <StatTile label="Прошлая неделя" value={fmtHdec(ins.previous_s)} />
        <div className="card px-4 py-3 flex-1 min-w-[120px]">
          <p className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">Динамика</p>
          <p className="text-2xl font-black mt-0.5 flex items-center gap-2" style={{ color: deltaColor }}>
            <DeltaIcon size={22} />
            {delta == null ? '—' : `${delta > 0 ? '+' : ''}${delta}%`}
          </p>
        </div>
      </div>

      {/* По дням: текущая неделя + «призрак» прошлой */}
      <div className="card p-4 mt-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">По дням</span>
          <span className="text-[10px] text-ink-dim">
            <span className="inline-block w-2.5 h-2.5 rounded-sm bg-accent mr-1 align-middle" />эта ·
            <span className="inline-block w-2.5 h-2.5 rounded-sm ml-2 mr-1 align-middle" style={{ background: '#2a3350' }} />прошлая
          </span>
        </div>
        <div className="grid grid-cols-7 gap-3 items-end h-40">
          {days.map((d) => (
            <div key={d.label} className="flex flex-col items-center justify-end h-full gap-1">
              <div className="w-full flex items-end justify-center gap-1 flex-1">
                <motion.div className="w-3 rounded-t-[3px]" style={{ background: '#2a3350' }}
                  initial={{ height: 0 }} animate={{ height: `${(d.prev / mx) * 100}%` }}
                  transition={{ type: 'spring', stiffness: 120, damping: 20 }}
                  title={`прошлая: ${fmtH(d.prev)}`} />
                <motion.div className="w-3 rounded-t-[3px]"
                  style={{ background: d.isToday ? '#00e676' : d.future ? '#1f263a' : '#4fc3f7' }}
                  initial={{ height: 0 }}
                  animate={{ height: `${Math.max((d.cur / mx) * 100, d.cur ? 3 : 0)}%` }}
                  transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.05 }}
                  title={`эта: ${fmtH(d.cur)}`} />
              </div>
              <span className={`text-[10px] font-mono ${d.isToday ? 'text-ok font-bold' : 'text-ink-dim'}`}>{d.label}</span>
              <span className="text-[10px] font-mono text-ink-soft">{d.cur ? fmtH(d.cur) : '·'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Топ проектов недели */}
      <div className="card p-4 mt-5">
        <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">Топ проектов недели</span>
        {ins.top_projects.length === 0 ? (
          <p className="text-sm text-ink-dim mt-3">На этой неделе сессий ещё не было.</p>
        ) : (
          <div className="mt-3 space-y-3">
            {ins.top_projects.map((t, i) => (
              <div key={t.id} className="flex items-center gap-3 cursor-pointer group"
                onClick={() => nav(`/project/${t.id}`)}>
                <span className="text-[11px] font-mono text-ink-dim w-4">{i + 1}</span>
                <span className="text-xl">{t.emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-baseline">
                    <p className="text-[13px] font-semibold truncate group-hover:text-accent transition-colors">{t.name}</p>
                    <span className="text-[12px] font-mono shrink-0 ml-2" style={{ color: t.color }}>{fmtH(t.total)}</span>
                  </div>
                  <div className="mt-1">
                    <ProgressBar pct={(t.total / topMax) * 100} color={t.color} h={6} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
