// Библиотека: сетка «капсул» проектов как в Steam + сводные плитки.
import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Plus } from 'lucide-react'
import { useStore } from '../store'
import { api } from '../api'
import { fmtHdec, fmtH, capsuleGradient, STATUS_META } from '../util'
import { StatTile } from '../components/bits'

export default function Library({ onNewProject }) {
  const { activities, timers, refresh } = useStore()
  const [overview, setOverview] = useState(null)
  const nav = useNavigate()

  useEffect(() => { api.overview().then(setOverview).catch(() => {}) }, [activities])

  const visible = useMemo(
    () => (activities || []).filter((a) => a.status !== 'deleted'),
    [activities])
  const deleted = useMemo(
    () => (activities || []).filter((a) => a.status === 'deleted'),
    [activities])

  const quickStart = async (e, aid) => {
    e.stopPropagation()
    await api.timer(aid, 'start')
    await refresh()
    nav(`/project/${aid}`)
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-end justify-between mb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Библиотека</h1>
          <p className="text-sm text-ink-dim mt-1">Твои проекты — как игры. Часы — как прогресс.</p>
        </div>
        <button onClick={onNewProject} className="btn bg-accent text-bg font-bold hover:brightness-110">
          <Plus size={16} strokeWidth={3} /> Новый проект
        </button>
      </div>

      {overview && (
        <div className="flex gap-3 mb-6 flex-wrap">
          <StatTile label="Общее время" value={fmtHdec(overview.total_s)} accent="#4fc3f7" />
          <StatTile label="Сегодня" value={fmtH(overview.today_s)} accent={overview.today_s ? '#00e676' : undefined} />
          <StatTile label="За 7 дней" value={fmtH(overview.week_s)} />
          <StatTile label="Сессий" value={overview.sessions} />
          <StatTile label="Проектов" value={visible.length} />
        </div>
      )}

      {activities !== null && visible.length === 0 && (
        <div className="card grid place-items-center py-20 text-center">
          <span className="text-5xl mb-3">⌚</span>
          <p className="font-bold text-lg">Библиотека пуста</p>
          <p className="text-sm text-ink-dim mt-1">Создай первый проект и запусти таймер</p>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {visible.map((a) => {
          const t = timers[a.id]
          const total = a.total_s + (t?.elapsed || 0)
          return (
            <div key={a.id} onClick={() => nav(`/project/${a.id}`)}
              className="capsule group relative aspect-[3/4] rounded-xl overflow-hidden cursor-pointer
                         border border-line hover:border-accent/40 hover:shadow-capsule">
              <div className="absolute inset-0" style={{ background: capsuleGradient(a.color) }} />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/20" />
              <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-[70%] text-6xl drop-shadow-lg
                               transition-transform duration-200 group-hover:scale-110">
                {a.emoji}
              </span>
              <div className="absolute inset-x-0 bottom-0 p-3">
                <p className="font-bold text-white text-sm leading-tight drop-shadow line-clamp-2">{a.name}</p>
                <p className={`text-[11px] font-mono mt-0.5 ${t?.running ? 'text-ok' : 'text-white/70'}`}>
                  {fmtHdec(total)} наиграно
                </p>
              </div>
              {a.status !== 'active' && (
                <span className={`chip absolute top-2 left-2 ${STATUS_META[a.status].chip} backdrop-blur`}>
                  {STATUS_META[a.status].label}
                </span>
              )}
              {t?.running && (
                <span className="absolute top-2.5 right-2.5 w-3 h-3 rounded-full bg-ok dot-live shadow-[0_0_10px_#00e676]" />
              )}
              {!t && a.status === 'active' && (
                <button onClick={(e) => quickStart(e, a.id)}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity
                             w-9 h-9 grid place-items-center rounded-lg play-btn text-bg"
                  title="Играть">
                  <Play size={16} fill="currentColor" />
                </button>
              )}
            </div>
          )
        })}
      </div>

      {deleted.length > 0 && (
        <details className="mt-8">
          <summary className="text-[11px] font-bold uppercase tracking-[0.16em] text-ink-dim cursor-pointer select-none">
            Удалённые · {deleted.length}
          </summary>
          <div className="mt-3 space-y-2">
            {deleted.map((a) => (
              <div key={a.id} className="card flex items-center gap-3 px-4 py-2.5">
                <span className="text-xl opacity-60">{a.emoji}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-ink-soft truncate">{a.name}</p>
                  <p className="text-[11px] text-ink-dim font-mono">{fmtH(a.total_s)} · {a.session_count} сессий</p>
                </div>
                <button className="btn-ghost !py-1.5 !text-xs"
                  onClick={async () => { await api.setStatus(a.id, 'active'); refresh() }}>
                  Восстановить
                </button>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
