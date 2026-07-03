// Модалки: базовая, проект (создание/редактирование), заметка, подтверждение.
import React, { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { EMOJIS, PROJECT_COLORS, fmtHMS } from '../util'

export function Modal({ title, onClose, children, width = 'max-w-md' }) {
  useEffect(() => {
    const h = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])
  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-black/60 backdrop-blur-sm" onMouseDown={onClose}>
      <div className={`card !bg-surf w-[92vw] ${width} shadow-capsule`} onMouseDown={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 pt-4 pb-1">
          <h3 className="font-bold text-[15px]">{title}</h3>
          <button onClick={onClose} className="text-ink-dim hover:text-ink transition-colors"><X size={18} /></button>
        </div>
        <div className="px-5 pb-5">{children}</div>
      </div>
    </div>
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

export function NoteModal({ duration, initial = '', onSave, onClose }) {
  const [note, setNote] = useState(initial)
  return (
    <Modal title={duration != null ? `Сессия завершена · ${fmtHMS(duration)}` : 'Заметка к сессии'} onClose={onClose}>
      <p className="text-xs text-ink-dim mb-2">Что делал? (Ctrl+Enter — сохранить)</p>
      <textarea autoFocus rows={4} className="input resize-none" value={note}
        onChange={(e) => setNote(e.target.value)}
        onKeyDown={(e) => e.ctrlKey && e.key === 'Enter' && onSave(note.trim())} />
      <div className="flex justify-end gap-2 pt-3">
        <button className="btn-ghost" onClick={() => onSave('')}>Пропустить</button>
        <button className="btn bg-ok text-bg font-bold hover:brightness-110" onClick={() => onSave(note.trim())}>
          Сохранить
        </button>
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
