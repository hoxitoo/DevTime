// Столбики активности за 28 дней. Одна серия — один хью (акцент проекта),
// скруглённые верхушки, тултип на hover, разреженные подписи дат.
import React, { useMemo, useState } from 'react'
import { fmtH, blend } from '../util'

const W = 820, H = 130, PAD_B = 22, PAD_T = 14

export default function ActivityChart({ daily, color = '#4fc3f7' }) {
  const [hover, setHover] = useState(null)

  const days = useMemo(() => {
    const map = Object.fromEntries((daily || []).map((r) => [r.day, r.total]))
    const out = []
    for (let i = 27; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i)
      const iso = d.toISOString().slice(0, 10)
      out.push({ iso, dom: d.getDate(), total: map[iso] || 0, today: i === 0 })
    }
    return out
  }, [daily])

  const mx = Math.max(1, ...days.map((d) => d.total))
  const bw = W / 28

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full block" role="img"
        aria-label="Активность за 28 дней">
        <line x1="0" y1={H - PAD_B} x2={W} y2={H - PAD_B} stroke="#242d42" strokeWidth="1" />
        {mx > 1 && (
          <text x={W - 4} y={PAD_T - 3} textAnchor="end" fontSize="10"
            fill="#5d6a8a" fontFamily="monospace">{fmtH(mx)}</text>
        )}
        {days.map((d, i) => {
          const frac = d.total / mx
          const bh = d.total ? Math.max(frac * (H - PAD_B - PAD_T), 3) : 0
          const x = i * bw + bw * 0.22
          const w = bw * 0.56
          const y = H - PAD_B - bh
          const fill = d.today ? '#00e676' : color
          const showTick = d.today || [1, 8, 15, 22].includes(d.dom)
          return (
            <g key={d.iso}>
              {bh > 0 && (
                <rect x={x} y={y} width={w} height={bh} rx="3"
                  fill={hover === i ? fill : blend(fill, '#151a26', 0.85)} />
              )}
              {/* хит-зона шире бара */}
              <rect x={i * bw} y="0" width={bw} height={H - PAD_B} fill="transparent"
                onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} />
              {showTick && (
                <text x={x + w / 2} y={H - 7} textAnchor="middle" fontSize="10"
                  fill={d.today ? '#00e676' : '#5d6a8a'} fontFamily="monospace">
                  {d.today ? 'сег' : String(d.dom).padStart(2, '0')}
                </text>
              )}
            </g>
          )
        })}
      </svg>
      {hover !== null && (
        <div className="absolute pointer-events-none bg-surf3 border border-line rounded-lg px-2.5 py-1.5 text-xs shadow-capsule z-10"
          style={{ left: `${(hover / 28) * 100}%`, top: -8, transform: hover > 20 ? 'translateX(-105%)' : 'translateX(6px)' }}>
          <span className="text-ink-soft">{days[hover].iso.slice(5)}</span>{' · '}
          <span className="font-bold text-ink">{days[hover].total ? fmtH(days[hover].total) : '—'}</span>
        </div>
      )}
    </div>
  )
}
