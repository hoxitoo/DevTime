import React, { useState } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import { StoreProvider, useStore } from './store'
import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import { Toasts } from './components/bits'
import { ProjectModal } from './components/Modal'
import Library from './pages/Library'
import Project from './pages/Project'
import Profile from './pages/Profile'
import Achievements from './pages/Achievements'
import { api } from './api'

function Shell() {
  const [newProject, setNewProject] = useState(false)
  const { refresh } = useStore()
  const nav = useNavigate()

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
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Library onNewProject={() => setNewProject(true)} />} />
            <Route path="/project/:id" element={<Project />} />
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
    <StoreProvider>
      <Shell />
    </StoreProvider>
  )
}
