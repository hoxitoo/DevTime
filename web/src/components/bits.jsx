// Мелкие переиспользуемые элементы: стат-плитка, прогресс-бар, тосты, счётчик.
import React, { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence, animate } from 'motion/react'
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
      <motion.div className="h-full rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, pct)}%` }}
        transition={{ type: 'spring', stiffness: 90, damping: 20 }}
        style={{ background: `linear-gradient(90deg, ${color}aa, ${color})` }} />
    </div>
  )
}

// Число, «набегающее» от 0 до value при появлении (game feel для XP/часов)
export function CountUp({ value, format = (v) => Math.round(v).toLocaleString('ru') }) {
  const [text, setText] = useState(format(0))
  const ref = useRef(null)
  useEffect(() => {
    const controls = animate(0, value, {
      duration: 0.9,
      ease: 'easeOut',
      onUpdate: (v) => setText(format(v)),
    })
    return () => controls.stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])
  return <span ref={ref}>{text}</span>
}

export function Toasts() {
  const { toasts } = useStore()
  return (
    <div className="fixed bottom-5 right-5 z-50 space-y-2 w-80">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div key={t.id} layout
            initial={{ opacity: 0, y: 24, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 60, transition: { duration: 0.18 } }}
            transition={{ type: 'spring', stiffness: 380, damping: 26 }}
            className={`glass rounded-xl px-4 py-3 flex items-center gap-3 shadow-capsule ${
              t.glow ? '!border-accent/60 shadow-glow' : ''}`}>
            <motion.span className="text-2xl"
              initial={{ scale: 0, rotate: -30 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 500, damping: 15, delay: 0.08 }}>
              {t.icon}
            </motion.span>
            <div className="min-w-0">
              <p className={`text-[11px] font-bold uppercase tracking-wider ${t.glow ? 'text-accent' : 'text-ink-dim'}`}>{t.title}</p>
              <p className="text-sm font-semibold truncate">{t.text}</p>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
