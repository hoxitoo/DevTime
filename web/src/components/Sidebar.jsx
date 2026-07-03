import React, { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Search, Plus, Play } from 'lucide-react'
import { useStore } from '../store'
import { api } from '../api'
import { fmtH, capsuleGradient, STATUS_META } from '../util'

export default function Sidebar({ onNewProject }) {
  const { activities, timers, refresh } = useStore()
  const [q, setQ] = useState('')
  const [filter, setFilter] = useState('active')
  const nav = useNavigate()
  const { id } = useParams()
  const selId = id ? Number(id) : null

  const list = useMemo(() => {
    let acts = activities || []
    if (filter === 'active') acts = acts.filter((a) => a.status === 'active')
    else acts = acts.filter((a) => a.status !== 'deleted')
    const query = q.trim().toLowerCase()
    if (query) acts = acts.filter((a) => a.name.toLowerCase().includes(query))
    return acts
  }, [activities, q, filter])

  const quickStart = async (e, aid) => {
    e.stopPropagation()
    await api.timer(aid, 'start')
    await refresh()
    nav(`/project/${aid}`)
  }

  return (
    <aside className="w-64 shrink-0 bg-sidebar border-r border-line flex flex-col">
      <div className="p-3 pb-2 flex items-center justify-between">
        <span className="text-[10px] font-bold tracking-[0.2em] text-ink-dim">БИБЛИОТЕКА</span>
        <button onClick={onNewProject}
          className="w-7 h-7 grid place-items-center rounded-lg bg-accent text-bg hover:brightness-110 transition"
          title="Новый проект">
          <Plus size={16} strokeWidth={3} />
        </button>
      </div>

      <div className="px-3 pb-2">
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-dim" />
          <input className="input !pl-8 !py-1.5 !text-[13px]" placeholder="Поиск..."
            value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="px-3 pb-2 flex gap-1.5">
        {[['active', 'Активные'], ['all', 'Все']].map(([k, label]) => (
          <button key={k} onClick={() => setFilter(k)}
            className={`flex-1 rounded-md py-1 text-[11px] font-bold transition-colors ${
              filter === k ? 'bg-accent text-bg' : 'bg-surf2 text-ink-dim hover:text-ink-soft'}`}>
            {label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-1.5">
        {activities === null && <p className="text-ink-dim text-xs text-center pt-8">Загрузка...</p>}
        {activities !== null && list.length === 0 && (
          <p className="text-ink-dim text-xs text-center pt-8 leading-5">
            {q ? 'Ничего не найдено' : <>Нет проектов.<br />Нажми <b>＋</b></>}
          </p>
        )}
        {list.map((a) => {
          const t = timers[a.id]
          const running = t?.running, paused = t?.paused
          const total = a.total_s + (t?.elapsed || 0)
          const sel = a.id === selId
          return (
            <div key={a.id} onClick={() => nav(`/project/${a.id}`)}
              className={`group relative rounded-lg overflow-hidden cursor-pointer border transition-colors ${
                sel ? 'border-accent/70' : 'border-transparent hover:border-line'}`}>
              <div className="flex items-center gap-2.5 px-2.5 py-2"
                style={{ background: capsuleGradient(a.color) }}>
                <span className="text-[22px] leading-none drop-shadow">{a.emoji}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-bold text-white truncate drop-shadow-sm">{a.name}</p>
                  <p className={`text-[11px] font-mono ${running ? 'text-ok' : paused ? 'text-warn' : 'text-white/70'}`}>
                    {fmtH(total)}
                    {a.status !== 'active' && (
                      <span className="ml-1.5 opacity-80">· {STATUS_META[a.status].label.toLowerCase()}</span>
                    )}
                  </p>
                </div>
                {running && <span className="w-2.5 h-2.5 rounded-full bg-ok dot-live shrink-0" />}
                {paused && <span className="text-warn text-xs shrink-0">⏸</span>}
                {!running && !paused && a.status === 'active' && (
                  <button onClick={(e) => quickStart(e, a.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity w-7 h-7 grid place-items-center
                               rounded-md bg-black/40 text-ok hover:bg-black/60 shrink-0"
                    title="Быстрый старт">
                    <Play size={14} fill="currentColor" />
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
