// Глобальное состояние: список проектов, тик таймеров, тосты, pomodoro.
import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { api } from './api'

const Ctx = createContext(null)
export const useStore = () => useContext(Ctx)

export function StoreProvider({ children }) {
  const [activities, setActivities] = useState(null) // null = загрузка
  const [timers, setTimers] = useState({})
  const [toasts, setToasts] = useState([])
  const [pomos, setPomos] = useState({}) // aid -> endTs(ms)
  const pomosRef = useRef(pomos)
  pomosRef.current = pomos

  const refresh = useCallback(async () => {
    try { setActivities(await api.activities()) } catch (e) { console.error(e) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  // Тик раз в секунду: состояние таймеров + отсчёт pomodoro + титул вкладки
  useEffect(() => {
    const t = setInterval(async () => {
      try {
        const ts = await api.timers()
        setTimers(ts)
        const running = Object.values(ts).filter((x) => x.running)
        if (running.length) {
          const el = Math.max(...running.map((x) => x.elapsed))
          const p = (n) => String(n).padStart(2, '0')
          document.title = `▶ ${p(Math.floor(el / 3600))}:${p(Math.floor((el % 3600) / 60))}:${p(el % 60)} · DevTime`
        } else if (Object.keys(ts).length) {
          document.title = '⏸ DevTime'
        } else if (document.title !== 'DevTime') {
          document.title = 'DevTime'
        }
      } catch { /* сервер перезапускается */ }
      const now = Date.now()
      const fired = Object.entries(pomosRef.current).filter(([, end]) => end <= now)
      if (fired.length) {
        setPomos((p) => {
          const n = { ...p }
          fired.forEach(([aid]) => delete n[aid])
          return n
        })
        fired.forEach(() => pushToast({ icon: '🍅', title: 'Pomodoro', text: 'Время вышло — сделай перерыв ☕' }))
      }
    }, 1000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const pushToast = useCallback((t) => {
    const id = Math.random().toString(36).slice(2)
    setToasts((ts) => [...ts, { id, ...t }])
    setTimeout(() => setToasts((ts) => ts.filter((x) => x.id !== id)), 6000)
  }, [])

  const celebrate = useCallback((achievements) => {
    (achievements || []).forEach((a, i) =>
      setTimeout(() => pushToast({
        icon: a.icon, title: 'Достижение получено!', text: a.title, glow: true,
      }), i * 700))
  }, [pushToast])

  const startPomo = useCallback((aid, minutes) => {
    setPomos((p) => ({ ...p, [aid]: Date.now() + minutes * 60_000 }))
  }, [])
  const cancelPomo = useCallback((aid) => {
    setPomos((p) => { const n = { ...p }; delete n[aid]; return n })
  }, [])

  const value = {
    activities, refresh, timers, toasts, pushToast, celebrate,
    pomos, startPomo, cancelPomo,
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
