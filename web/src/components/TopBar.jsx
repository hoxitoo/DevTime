import React, { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Download } from 'lucide-react'
import { api } from '../api'

export default function TopBar() {
  const [profile, setProfile] = useState(null)
  useEffect(() => { api.profile().then(setProfile).catch(() => {}) }, [])

  const tab = ({ isActive }) => 'nav-tab' + (isActive ? ' active' : '')

  return (
    <header className="h-14 shrink-0 bg-sidebar border-b border-line flex items-center px-4 gap-2 z-20">
      <div className="flex items-center gap-2 pr-4">
        <span className="text-xl">⌚</span>
        <span className="font-black tracking-[0.18em] text-[15px]">DEVTIME</span>
      </div>

      <nav className="flex items-center gap-1">
        <NavLink to="/" end className={tab}>Библиотека</NavLink>
        <NavLink to="/profile" className={tab}>Профиль</NavLink>
        <NavLink to="/achievements" className={tab}>Ачивки</NavLink>
      </nav>

      <div className="ml-auto flex items-center gap-3">
        {profile && (
          <NavLink to="/profile"
            className="flex items-center gap-2 bg-surf2 border border-line rounded-lg px-3 py-1.5 hover:border-accent/50 transition-colors">
            <span className="text-[11px] uppercase tracking-wider text-ink-dim font-bold">{profile.rank}</span>
            <span className="w-7 h-7 rounded-full grid place-items-center text-[11px] font-black text-bg"
              style={{ background: 'linear-gradient(135deg,#4fc3f7,#7c4dff)' }}>
              {profile.level}
            </span>
          </NavLink>
        )}
        <a href="/api/export.csv" className="btn-ghost !py-1.5" title="Экспорт всех сессий в CSV">
          <Download size={15} /> CSV
        </a>
      </div>
    </header>
  )
}
