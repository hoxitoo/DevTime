import React, { useState } from 'react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { MotionConfig } from 'motion/react'
import { StoreProvider, useStore } from './store'
import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import { Toasts } from './components/bits'
import { ProjectModal } from './components/Modal'
import Library from './pages/Library'
import Project from './pages/Project'
import Profile from './pages/Profile'
import Week from './pages/Week'
import Achievements from './pages/Achievements'
import { api } from './api'

function Shell() {
  const [newProject, setNewProject] = useState(false)
  const { refresh } = useStore()
  const nav = useNavigate()
  const location = useLocation()

  // Глобальные хоткеи: / — поиск, N — новый проект (вне полей ввода)
  React.useEffect(() => {
    const h = (e) => {
      const tag = e.target.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable) return
      if (e.key === '/') {
        e.preventDefault()
        document.querySelector('input[placeholder="Поиск..."]')?.focus()
      } else if (e.key.toLowerCase() === 'n' || e.key.toLowerCase() === 'т') {
        e.preventDefault()
        setNewProject(true)
      }
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [])

  const createProject = async (body) => {
    const a = await api.create(body)
    setNewProject(false)
    await refresh()
    nav(`/project/${a.id}`)
  }

  return (
    <div className="h-full flex flex-col">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Routes>
          <Route path="/project/:id" element={<Sidebar onNewProject={() => setNewProject(true)} />} />
          <Route path="*" element={<Sidebar onNewProject={() => setNewProject(true)} />} />
        </Routes>
        <main className="flex-1 overflow-y-auto page-enter" key={location.pathname}>
          <Routes>
            <Route path="/" element={<Library onNewProject={() => setNewProject(true)} />} />
            <Route path="/project/:id" element={<Project />} />
            <Route path="/week" element={<Week />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/achievements" element={<Achievements />} />
          </Routes>
        </main>
      </div>
      <Toasts />
      {newProject && <ProjectModal onSave={createProject} onClose={() => setNewProject(false)} />}
    </div>
  )
}

export default function App() {
  return (
    // reducedMotion="user" — Motion сам отключит анимации при prefers-reduced-motion
    <MotionConfig reducedMotion="user">
      <StoreProvider>
        <Shell />
      </StoreProvider>
    </MotionConfig>
  )
}
