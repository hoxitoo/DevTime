// Модалки: базовая, проект (создание/редактирование), заметка, подтверждение.
import React, { useEffect, useState } from 'react'
import { motion } from 'motion/react'
import { X } from 'lucide-react'
import { EMOJIS, PROJECT_COLORS, fmtHMS } from '../util'

export function Modal({ title, onClose, children, width = 'max-w-md' }) {
  useEffect(() => {
    const h = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])
  return (
    <motion.div className="fixed inset-0 z-40 grid place-items-center bg-black/60 backdrop-blur-sm"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.15 }}
      onMouseDown={onClose}>
      <motion.div className={`glass rounded-xl w-[92vw] ${width} shadow-capsule`}
        initial={{ opacity: 0, scale: 0.94, y: 14 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 420, damping: 30 }}
        onMouseDown={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-4 pb-1">
          <h3 className="font-bold text-[15px]">{title}</h3>
          <button onClick={onClose} aria-label="Закрыть" className="text-ink-dim hover:text-ink transition-colors"><X size={18} /></button>
        </div>
        <div className="px-5 pb-5">{children}</div>
      </motion.div>
    </motion.div>
  )
}

export function ProjectModal({ act, onSave, onClose }) {
  const [name, setName] = useState(act?.name || '')
  const [emoji, setEmoji] = useState(act?.emoji || '💻')
  const [color, setColor] = useState(act?.color || PROJECT_COLORS[0])
  const [goal, setGoal] = useState(act?.goal_h ? String(act.goal_h) : '')

  const submit = () => {
    if (!name.trim()) return
    onSave({ name: name.trim(), emoji, color, goal_h: parseFloat(goal) || 0 })
  }

  return (
    <Modal title={act ? 'Редактировать проект' : 'Новый проект'} onClose={onClose}>
      <div className="space-y-4" onKeyDown={(e) => e.key === 'Enter' && submit()}>
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wider text-ink-dim">Название</label>
          <input autoFocus className="input mt-1" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Мой проект" />
        </div>
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wider text-ink-dim">Иконка</label>
          <div className="grid grid-cols-10 gap-1 mt-1">
            {EMOJIS.map((em) => (
              <button key={em} onClick={() => setEmoji(em)}
                className={`h-9 rounded-lg grid place-items-center text-lg transition-colors ${
                  em === emoji ? 'bg-accent/25 ring-1 ring-accent' : 'bg-surf2 hover:bg-surf3'}`}>
                {em}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wider text-ink-dim">Цвет акцента</label>
          <div className="flex gap-2 mt-1.5">
            {PROJECT_COLORS.map((c) => (
              <button key={c} onClick={() => setColor(c)}
                className={`w-7 h-7 rounded-full transition-transform ${c === color ? 'ring-2 ring-white scale-110' : 'hover:scale-110'}`}
                style={{ background: c }} />
            ))}
          </div>
        </div>
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wider text-ink-dim">Цель, часов (пусто = нет)</label>
          <input className="input mt-1 w-28" value={goal} onChange={(e) => setGoal(e.target.value)}
            placeholder="100" inputMode="decimal" />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button className="btn-ghost" onClick={onClose}>Отмена</button>
          <button className="btn bg-accent text-bg font-bold hover:brightness-110" onClick={submit}>
            Сохранить
          </button>
        </div>
      </div>
    </Modal>
  )
}

const LONG_SESSION_S = 6 * 3600  // >6ч — вероятно, забытый таймер

export function NoteModal({ duration, initial = '', onSave, onClose }) {
  const [note, setNote] = useState(initial)
  const isLong = duration != null && duration > LONG_SESSION_S
  const [hours, setHours] = useState(isLong ? (duration / 3600).toFixed(1) : null)

  const save = (n) => {
    // при длинной сессии отдаём и скорректированную длительность
    const trimmed = isLong ? Math.round(Math.min(parseFloat(hours) || 0, duration / 3600) * 3600) : undefined
    onSave(n, trimmed && trimmed > 0 && trimmed !== duration ? trimmed : undefined)
  }

  return (
    <Modal title={duration != null ? `Сессия завершена · ${fmtHMS(duration)}` : 'Заметка к сессии'} onClose={onClose}>
      {isLong && (
        <div className="mb-3 rounded-lg border border-warn/50 bg-warn/10 px-3 py-2.5">
          <p className="text-[13px] text-warn font-semibold">⚠ Сессия длиннее 6 часов — забытый таймер?</p>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-ink-soft">Засчитать</span>
            <input className="input !w-20 !py-1 text-center" value={hours} inputMode="decimal"
              onChange={(e) => setHours(e.target.value)} />
            <span className="text-xs text-ink-soft">ч из {(duration / 3600).toFixed(1)}</span>
          </div>
        </div>
      )}
      <p className="text-xs text-ink-dim mb-2">Что делал? (Ctrl+Enter — сохранить)</p>
      <textarea autoFocus rows={4} className="input resize-none" value={note}
        onChange={(e) => setNote(e.target.value)}
        onKeyDown={(e) => e.ctrlKey && e.key === 'Enter' && save(note.trim())} />
      <div className="flex justify-end gap-2 pt-3">
        <button className="btn-ghost" onClick={() => save('')}>Пропустить</button>
        <button className="btn bg-ok text-bg font-bold hover:brightness-110" onClick={() => save(note.trim())}>
          Сохранить
        </button>
      </div>
    </Modal>
  )
}

// Ручное добавление/правка сессии («забыл нажать СТАРТ»)
export function SessionModal({ session, onSave, onDelete, onClose }) {
  const toLocalInput = (s) => (s || '').slice(0, 16).replace(' ', 'T')
  const now = new Date()
  const defStart = new Date(now.getTime() - 3600_000)
  const pad = (n) => String(n).padStart(2, '0')
  const defLocal = `${defStart.getFullYear()}-${pad(defStart.getMonth() + 1)}-${pad(defStart.getDate())}T${pad(defStart.getHours())}:${pad(defStart.getMinutes())}`

  const [start, setStart] = useState(session ? toLocalInput(session.started_at) : defLocal)
  const [minutes, setMinutes] = useState(session ? String(Math.round(session.duration_s / 60)) : '60')
  const [note, setNote] = useState(session?.note || '')

  const submit = () => {
    const m = parseInt(minutes, 10)
    if (!start || !m || m <= 0) return
    onSave({
      started_at: start.replace('T', ' ') + ':00',
      duration_min: m,
      note: note.trim(),
    })
  }

  return (
    <Modal title={session ? 'Редактировать сессию' : 'Добавить сессию'} onClose={onClose}>
      <div className="space-y-3">
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wider text-ink-dim">Начало</label>
          <input type="datetime-local" className="input mt-1" value={start}
            onChange={(e) => setStart(e.target.value)} />
        </div>
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wider text-ink-dim">Длительность, минут</label>
          <input className="input mt-1 w-28" value={minutes} inputMode="numeric"
            onChange={(e) => setMinutes(e.target.value)} />
        </div>
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wider text-ink-dim">Заметка</label>
          <textarea rows={2} className="input mt-1 resize-none" value={note}
            onChange={(e) => setNote(e.target.value)} placeholder="Что делал..." />
        </div>
        <div className="flex justify-between gap-2 pt-1">
          {session && onDelete ? (
            <button className="btn-danger" onClick={onDelete}>Удалить</button>
          ) : <span />}
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={onClose}>Отмена</button>
            <button className="btn bg-accent text-bg font-bold hover:brightness-110" onClick={submit}>
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </Modal>
  )
}

export function ConfirmModal({ title, text, confirmLabel = 'Да', danger, onConfirm, onClose }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="text-sm text-ink-soft leading-6 whitespace-pre-line">{text}</p>
      <div className="flex justify-end gap-2 pt-4">
        <button className="btn-ghost" onClick={onClose}>Отмена</button>
        <button className={danger ? 'btn-danger' : 'btn bg-accent text-bg font-bold hover:brightness-110'}
          onClick={onConfirm}>{confirmLabel}</button>
      </div>
    </Modal>
  )
}
