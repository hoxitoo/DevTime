// Страница проекта — «страница игры»: hero-баннер, PLAY-бар, статистика,
// цель, график, план дня, история сессий; справа — о проекте и pomodoro.
import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Pause, Play, Square, Pencil, Trash2, RotateCcw, Flag, Timer } from 'lucide-react'
import { useStore } from '../store'
import { api } from '../api'
import { fmtH, fmtHdec, fmtHMS, fmtDate, heroGradient, STATUS_META } from '../util'
import { StatTile, ProgressBar } from '../components/bits'
import { ProjectModal, NoteModal, ConfirmModal, SessionModal } from '../components/Modal'
import ActivityChart from '../components/ActivityChart'

export default function Project() {
  const { id } = useParams()
  const aid = Number(id)
  const nav = useNavigate()
  const { timers, refresh, celebrate, pushToast, pomos, startPomo, cancelPomo } = useStore()

  const [act, setAct] = useState(null)
  const [modal, setModal] = useState(null) // 'edit' | 'note' | 'confirm-*' | {editNote}
  const [noteCtx, setNoteCtx] = useState(null) // {sid, duration, initial}
  const [sessCtx, setSessCtx] = useState(null) // null=add | session-объект=edit
  const [plan, setPlan] = useState('')
  const [planSaved, setPlanSaved] = useState(false)
  const [desc, setDesc] = useState('')
  const [descEdit, setDescEdit] = useState(false)
  const [busy, setBusy] = useState(false) // защита от двойного клика (UX #32)

  // Единая обёртка: блокирует повторные клики и показывает ошибки тостом (UX #33)
  const guard = async (fn) => {
    if (busy) return
    setBusy(true)
    try { await fn() }
    catch (e) { pushToast({ icon: '⚠️', title: 'Ошибка', text: e.message }) }
    finally { setBusy(false) }
  }

  const load = useCallback(async () => {
    try {
      const a = await api.activity(aid)
      setAct(a); setPlan(a.day_plan || ''); setDesc(a.descr || '')
    } catch { nav('/') }
  }, [aid, nav])

  useEffect(() => { load() }, [load])

  // Хоткей Space: старт / пауза / продолжить (вне полей ввода).
  // Обработчик в ref, чтобы слушатель видел актуальное состояние.
  const spaceRef = React.useRef(() => {})
  useEffect(() => {
    const h = (e) => {
      if (e.code !== 'Space') return
      const tag = e.target.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable) return
      e.preventDefault()
      spaceRef.current()
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [])

  if (!act) return <div className="p-8 text-ink-dim text-sm">Загрузка...</div>

  const t = timers[aid]
  const running = t?.running, paused = t?.paused, elapsed = t?.elapsed || 0
  const liveTotal = act.total_s + elapsed
  const liveToday = act.today_s + elapsed
  const status = act.status
  const goalS = act.goal_h * 3600
  const goalPct = goalS ? Math.min(100, (liveTotal / goalS) * 100) : 0
  const pomoEnd = pomos[aid]
  const pomoLeft = pomoEnd ? Math.max(0, Math.floor((pomoEnd - Date.now()) / 1000)) : null

  const doTimer = (action) => guard(async () => {
    await api.timer(aid, action); await refresh(); await load()
  })

  // Space: старт / пауза / продолжить
  spaceRef.current = () => {
    if (busy || modal) return
    if (running) doTimer('pause')
    else if (paused) doTimer('resume')
    else if (status === 'active') doTimer('start')
  }

  const doStop = () => guard(async () => {
    const res = await api.stop(aid, '')
    await refresh(); await load()
    cancelPomo(aid)
    celebrate(res.new_achievements)
    setNoteCtx({ sid: res.session_id, duration: res.duration_s, initial: '' })
    setModal('note')
  })

  const saveNote = async (note, trimmedS) => {
    try {
      if (noteCtx) {
        if (trimmedS) {
          // забытый таймер: обрезаем длительность вместе с заметкой
          await api.patchSession(noteCtx.sid, { duration_s: trimmedS, note })
          pushToast({ icon: '✂️', title: 'Сессия обрезана', text: `Засчитано ${Math.round(trimmedS / 360) / 10}ч` })
        } else if (note) {
          await api.sessionNote(noteCtx.sid, note)
        }
      }
    } catch (e) { pushToast({ icon: '⚠️', title: 'Ошибка', text: e.message }) }
    setModal(null); setNoteCtx(null)
    await refresh(); await load()
  }

  // Ручные сессии: добавление / правка / удаление
  const saveSession = async (body) => {
    try {
      if (sessCtx) {
        await api.patchSession(sessCtx.id, {
          started_at: body.started_at, duration_s: body.duration_min * 60, note: body.note,
        })
      } else {
        const res = await api.addSession(aid, body)
        celebrate(res.new_achievements)
      }
      setModal(null); setSessCtx(null)
      await refresh(); await load()
    } catch (e) { pushToast({ icon: '⚠️', title: 'Ошибка', text: e.message }) }
  }

  const deleteSession = async () => {
    try {
      await api.deleteSession(sessCtx.id)
      pushToast({ icon: '🗑️', title: 'Сессия удалена', text: 'Время пересчитано' })
      setModal(null); setSessCtx(null)
      await refresh(); await load()
    } catch (e) { pushToast({ icon: '⚠️', title: 'Ошибка', text: e.message }) }
  }

  const setStatus = async (s) => {
    await api.setStatus(aid, s)
    setModal(null); await refresh(); await load()
    if (s === 'deleted') nav('/')
  }

  const savePlan = async () => {
    await api.savePlan(aid, plan)
    setPlanSaved(true); setTimeout(() => setPlanSaved(false), 1500)
    await load()
  }

  const saveDesc = async () => {
    await api.saveDescription(aid, desc)
    setDescEdit(false); await load()
  }

  const saveEdit = async (body) => {
    await api.update(aid, body)
    setModal(null); await refresh(); await load()
  }

  const today = new Date().toISOString().slice(0, 10)
  const planStale = act.day_plan && act.day_plan_date && act.day_plan_date < today

  return (
    <div>
      {/* ── Hero ── */}
      <div className="relative h-52 overflow-hidden" style={{ background: heroGradient(act.color) }}>
        <div className="absolute inset-0 opacity-[0.07]"
          style={{ backgroundImage: 'repeating-linear-gradient(0deg,#000 0 1px,transparent 1px 4px)' }} />
        <div className="absolute inset-0 bg-gradient-to-t from-bg via-transparent to-transparent" />
        <div className="absolute bottom-5 left-7 flex items-end gap-5">
          <span className="text-[64px] leading-none drop-shadow-xl">{act.emoji}</span>
          <div className="pb-1">
            <h1 className="text-3xl font-black text-white drop-shadow tracking-tight">{act.name}</h1>
            <p className="text-[12px] font-mono mt-1.5">
              {running && <span className="text-ok font-bold">● ИДЁТ СЕССИЯ</span>}
              {paused && <span className="text-warn font-bold">⏸ ПАУЗА</span>}
              {!running && !paused && (
                <span className={STATUS_META[status].cls + ' font-bold uppercase'}>{STATUS_META[status].label}</span>
              )}
              <span className="text-white/50 ml-3">в библиотеке с {fmtDate(act.created)}</span>
            </p>
          </div>
        </div>
        <div className="absolute top-4 right-5 flex gap-2">
          <button className="w-9 h-9 grid place-items-center rounded-lg bg-black/30 text-white/70 hover:text-white hover:bg-black/50 transition backdrop-blur"
            onClick={() => setModal('edit')} aria-label="Редактировать" title="Редактировать"><Pencil size={15} /></button>
          {status !== 'deleted' && (
            <button className="w-9 h-9 grid place-items-center rounded-lg bg-black/30 text-white/70 hover:text-danger hover:bg-black/50 transition backdrop-blur"
              onClick={() => setModal('confirm-delete')} aria-label="Переместить в удалённые" title="В удалённые"><Trash2 size={15} /></button>
          )}
        </div>
      </div>

      {/* ── PLAY-бар ── */}
      <div className="bg-surf border-y border-line px-7 py-4 flex items-center gap-5 flex-wrap">
        {running && (
          <>
            <button className="btn-ghost !w-12 !h-12 !p-0 !text-warn !border-warn/50" onClick={() => doTimer('pause')} disabled={busy} aria-label="Пауза" title="Пауза">
              <Pause size={20} />
            </button>
            <button className="btn-ghost !w-12 !h-12 !p-0 !text-danger !border-danger/50" onClick={doStop} disabled={busy} aria-label="Стоп" title="Стоп">
              <Square size={18} fill="currentColor" />
            </button>
            <span className="text-3xl font-black font-mono text-ok tabular-nums">{fmtHMS(elapsed)}</span>
          </>
        )}
        {paused && (
          <>
            <button className="play-btn btn !w-12 !h-12 !p-0 text-bg" onClick={() => doTimer('resume')} disabled={busy} aria-label="Продолжить" title="Продолжить">
              <Play size={20} fill="currentColor" />
            </button>
            <button className="btn-ghost !w-12 !h-12 !p-0 !text-danger !border-danger/50" onClick={doStop} disabled={busy} aria-label="Стоп" title="Стоп">
              <Square size={18} fill="currentColor" />
            </button>
            <span className="text-2xl font-black font-mono text-warn tabular-nums">⏸ {fmtHMS(elapsed)}</span>
          </>
        )}
        {!running && !paused && status === 'active' && (
          <button className="play-btn btn !px-10 !py-3.5 !text-base font-black text-bg tracking-wide"
            onClick={() => doTimer('start')} disabled={busy}>
            <Play size={20} fill="currentColor" /> ИГРАТЬ
          </button>
        )}
        {status === 'completed' && (
          <button className="btn-ghost !text-accent !border-accent/50" onClick={() => setStatus('active')}>
            <RotateCcw size={15} /> Вернуть в активные
          </button>
        )}
        {status === 'deleted' && (
          <button className="btn bg-accent text-bg font-bold" onClick={() => setStatus('active')}>
            <RotateCcw size={15} /> Восстановить
          </button>
        )}

        <div className="ml-auto flex items-center gap-2">
          <Timer size={15} className="text-ink-dim" />
          {pomoLeft != null ? (
            <button className="chip bg-warn/15 text-warn !text-[13px] font-mono" onClick={() => cancelPomo(aid)}
              title="Отменить pomodoro">
              🍅 {fmtHMS(pomoLeft)}
            </button>
          ) : (
            [25, 50, 90].map((m) => (
              <button key={m} className="btn-ghost !py-1 !px-2.5 !text-xs"
                onClick={() => { startPomo(aid, m); if (!t && status === 'active') doTimer('start') }}>
                {m}м
              </button>
            ))
          )}
        </div>
      </div>

      <div className="p-6 grid gap-5 lg:grid-cols-[1fr_290px] max-w-6xl">
        <div className="space-y-5 min-w-0">
          {/* Статистика */}
          <div className="flex gap-3 flex-wrap">
            <StatTile label="Всего" value={fmtHdec(liveTotal)} accent={act.color} />
            <StatTile label="Сегодня" value={fmtH(liveToday)} accent={liveToday ? '#00e676' : undefined} />
            <StatTile label="Неделя" value={fmtH(act.week_s)} />
            <StatTile label="Streak" value={`${act.streak}д ${act.streak >= 3 ? '🔥' : ''}`}
              accent={act.streak >= 3 ? '#ffab40' : undefined} />
            <StatTile label="Сессий" value={act.session_count} />
          </div>

          {/* Цель */}
          {goalS > 0 && (
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">🎯 Цель</span>
                <span className="text-sm font-bold" style={{ color: goalPct >= 100 ? '#00e676' : act.color }}>
                  {(liveTotal / 3600).toFixed(1)} / {act.goal_h} ч · {Math.floor(goalPct)}%
                </span>
              </div>
              <ProgressBar pct={goalPct} color={goalPct >= 100 ? '#00e676' : act.color} />
            </div>
          )}

          {/* График */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">📊 Активность</span>
              <span className="text-[10px] text-ink-dim">28 дней</span>
            </div>
            <ActivityChart daily={act.daily} color={act.color} />
          </div>

          {/* План дня */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">
                📌 План на сегодня
                {planStale && (
                  <span className="chip bg-warn/15 text-warn ml-2 !tracking-normal">
                    от {fmtDate(act.day_plan_date)}
                  </span>
                )}
              </span>
              <div className="flex gap-1.5">
                {planStale && (
                  <button className="btn-ghost !py-1 !px-3 !text-xs !text-warn"
                    onClick={() => { setPlan(''); api.savePlan(aid, '').then(load) }}>
                    Очистить
                  </button>
                )}
                <button className={`btn-ghost !py-1 !px-3 !text-xs ${planSaved ? '!text-ok !border-ok/50' : ''}`}
                  onClick={savePlan}>{planSaved ? '✓ Сохранено' : 'Сохранить'}</button>
              </div>
            </div>
            <textarea rows={3} className="input resize-none" value={plan}
              onChange={(e) => setPlan(e.target.value)} placeholder="Что нужно сделать сегодня..." />
          </div>

          {/* История сессий */}
          <div className="card p-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">История сессий</span>
              <button className="btn-ghost !py-1 !px-3 !text-xs"
                onClick={() => { setSessCtx(null); setModal('session') }}>
                ＋ Добавить забытую
              </button>
            </div>
            {act.sessions.length === 0 && (
              <p className="text-sm text-ink-dim mt-3">Нет сессий — жми ИГРАТЬ</p>
            )}
            <div className="mt-2 divide-y divide-line/60">
              {act.sessions.map((s) => (
                <div key={s.id} className="flex items-center gap-3 py-2.5 group">
                  <span className="text-[12px] font-mono text-ink-dim w-[118px] shrink-0">
                    {(s.started_at || '?').slice(0, 16)}
                  </span>
                  <span className="chip !normal-case !tracking-normal font-mono"
                    style={{ background: `${act.color}22`, color: act.color }}>
                    {fmtHMS(s.duration_s)}
                  </span>
                  <span className={`text-[13px] truncate flex-1 ${s.note ? 'text-ink-soft' : 'text-ink-dim'}`}>
                    {s.note || '—'}
                  </span>
                  <button className="opacity-0 group-hover:opacity-100 text-ink-dim hover:text-ink transition"
                    onClick={() => { setSessCtx(s); setModal('session') }}
                    aria-label="Редактировать сессию" title="Редактировать сессию">
                    <Pencil size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Правая колонка ── */}
        <div className="space-y-4">
          <div className="card p-4">
            <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">О проекте</span>
            <dl className="mt-3 space-y-2.5 text-[13px]">
              <div className="flex justify-between"><dt className="text-ink-dim">Статус</dt>
                <dd><span className={`chip ${STATUS_META[status].chip}`}>{STATUS_META[status].label}</span></dd></div>
              <div className="flex justify-between"><dt className="text-ink-dim">Создан</dt>
                <dd className="font-mono">{fmtDate(act.created)}</dd></div>
              <div className="flex justify-between"><dt className="text-ink-dim">Цель</dt>
                <dd className="font-mono">{act.goal_h ? `${act.goal_h} ч` : '—'}</dd></div>
              <div className="flex justify-between"><dt className="text-ink-dim">Наиграно</dt>
                <dd className="font-mono font-bold" style={{ color: act.color }}>{fmtHdec(liveTotal)}</dd></div>
            </dl>
            <div className="mt-4 space-y-2">
              {status === 'active' && (
                <button className="btn-ghost w-full !text-ok !border-ok/40" onClick={() => setModal('confirm-complete')}>
                  <Flag size={14} /> Завершить проект
                </button>
              )}
              <button className="btn-ghost w-full" onClick={() => setModal('edit')}>
                <Pencil size={14} /> Редактировать
              </button>
            </div>
          </div>

          {/* Описание — витрина проекта */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold tracking-[0.16em] text-ink-dim uppercase">Описание</span>
              {descEdit ? (
                <button className="btn-ghost !py-1 !px-3 !text-xs !text-ok" onClick={saveDesc}>Сохранить</button>
              ) : (
                <button className="btn-ghost !py-1 !px-3 !text-xs" onClick={() => setDescEdit(true)}>
                  {act.descr ? 'Изменить' : 'Добавить'}
                </button>
              )}
            </div>
            {descEdit ? (
              <textarea autoFocus rows={5} className="input resize-none text-[13px]" value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="О чём этот проект, стек, цели..." />
            ) : act.descr ? (
              <p className="text-[13px] text-ink-soft leading-5 whitespace-pre-line">{act.descr}</p>
            ) : (
              <p className="text-[12px] text-ink-dim">Пусто — расскажи, о чём проект, как на странице игры в Steam.</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Модалки ── */}
      {modal === 'edit' && <ProjectModal act={act} onSave={saveEdit} onClose={() => setModal(null)} />}
      {modal === 'note' && noteCtx && (
        <NoteModal duration={noteCtx.duration} initial={noteCtx.initial}
          onSave={saveNote} onClose={() => { setModal(null); setNoteCtx(null) }} />
      )}
      {modal === 'session' && (
        <SessionModal session={sessCtx} onSave={saveSession}
          onDelete={sessCtx ? deleteSession : undefined}
          onClose={() => { setModal(null); setSessCtx(null) }} />
      )}
      {modal === 'confirm-delete' && (
        <ConfirmModal title="Переместить в удалённые?" danger confirmLabel="Удалить"
          text={`«${act.name}» уйдёт в удалённые.\nСессии сохранятся, проект можно восстановить.${t ? '\n\n⚠ Активная сессия будет сохранена автоматически.' : ''}`}
          onConfirm={() => setStatus('deleted')} onClose={() => setModal(null)} />
      )}
      {modal === 'confirm-complete' && (
        <ConfirmModal title="Завершить проект?" confirmLabel="Завершить"
          text={`Отметить «${act.name}» как завершённый — как пройденную игру. Вернуть в активные можно в любой момент.`}
          onConfirm={() => setStatus('completed')} onClose={() => setModal(null)} />
      )}
    </div>
  )
}
