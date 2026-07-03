// Heatmap активности как на GitHub: 53 недели × 7 дней, sequential-шкала
// одного хью (акцент) на тёмной поверхности, тултип на hover.
import React, { useMemo, useState } from 'react'
import { fmtH, blend } from '../util'

const CELL = 12, GAP = 3
const LEVELS = ['#1a2030',
  blend('#4fc3f7', '#151a26', 0.36),
  blend('#4fc3f7', '#151a26', 0.56),
  blend('#4fc3f7', '#151a26', 0.78),
  '#4fc3f7']
const MONTHS = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']

function level(total, mx) {
  if (!total) return 0
  const f = total / mx
  return f > 0.75 ? 4 : f > 0.45 ? 3 : f > 0.2 ? 2 : 1
}

export default function Heatmap({ daily }) {
  const [hover, setHover] = useState(null)

  const { weeks, mx, monthTicks } = useMemo(() => {
    const map = Object.fromEntries((daily || []).map((r) => [r.day, r.total]))
    const today = new Date()
    const end = new Date(today)
    end.setDate(end.getDate() + (6 - ((today.getDay() + 6) % 7))) // до конца недели (пн-вс)
    const start = new Date(end)
    start.setDate(start.getDate() - 53 * 7 + 1)
    const weeks = []
    const monthTicks = []
    let cur = new Date(start)
    for (let w = 0; w < 53; w++) {
      const col = []
      for (let d = 0; d < 7; d++) {
        const iso = cur.toISOString().slice(0, 10)
        col.push({ iso, total: map[iso] || 0, future: cur > today })
        if (cur.getDate() === 1) monthTicks.push({ w, label: MONTHS[cur.getMonth()] })
        cur.setDate(cur.getDate() + 1)
      }
      weeks.push(col)
    }
    const mx = Math.max(1, ...Object.values(map))
    return { weeks, mx, monthTicks }
  }, [daily])

  const width = 53 * (CELL + GAP) + 20
  const height = 7 * (CELL + GAP) + 18

  return (
    <div className="relative overflow-x-auto">
      <svg width={width} height={height} className="block" role="img" aria-label="Активность за год">
        {monthTicks.map((m, i) => (
          <text key={i} x={20 + m.w * (CELL + GAP)} y={9} fontSize="9" fill="#5d6a8a">{m.label}</text>
        ))}
        {['пн', 'ср', 'пт'].map((d, i) => (
          <text key={d} x={0} y={14 + (i * 2 + 0.8) * (CELL + GAP) + 8} fontSize="9" fill="#5d6a8a">{d}</text>
        ))}
        {weeks.map((col, w) => col.map((c, d) => !c.future && (
          <rect key={c.iso} x={20 + w * (CELL + GAP)} y={14 + d * (CELL + GAP)}
            width={CELL} height={CELL} rx="2.5"
            fill={LEVELS[level(c.total, mx)]}
            stroke={hover?.iso === c.iso ? '#4fc3f7' : 'none'} strokeWidth="1.5"
            onMouseEnter={(e) => setHover({ ...c, x: e.clientX, y: e.clientY })}
            onMouseLeave={() => setHover(null)} />
        )))}
      </svg>
      <div className="flex items-center gap-1.5 mt-2 text-[10px] text-ink-dim justify-end pr-1">
        меньше {LEVELS.map((c, i) => (
          <span key={i} className="w-2.5 h-2.5 rounded-[3px] inline-block" style={{ background: c }} />
        ))} больше
      </div>
      {hover && (
        <div className="fixed pointer-events-none bg-surf3 border border-line rounded-lg px-2.5 py-1.5 text-xs shadow-capsule z-50"
          style={{ left: hover.x + 12, top: hover.y - 34 }}>
          <span className="text-ink-soft">{hover.iso}</span>{' · '}
          <span className="font-bold text-ink">{hover.total ? fmtH(hover.total) : 'нет активности'}</span>
        </div>
      )}
    </div>
  )
}
