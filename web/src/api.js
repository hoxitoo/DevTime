// Тонкий клиент REST API.

async function req(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'content-type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  activities: () => req('/api/activities'),
  activity: (id) => req(`/api/activities/${id}`),
  create: (body) => req('/api/activities', { method: 'POST', body }),
  update: (id, body) => req(`/api/activities/${id}`, { method: 'PUT', body }),
  savePlan: (id, text) => req(`/api/activities/${id}/plan`, { method: 'POST', body: { text } }),
  setStatus: (id, status) => req(`/api/activities/${id}/status`, { method: 'POST', body: { status } }),
  timer: (id, action) => req(`/api/activities/${id}/timer`, { method: 'POST', body: { action } }),
  stop: (id, note = '') => req(`/api/activities/${id}/stop`, { method: 'POST', body: { note } }),
  timers: () => req('/api/timers'),
  sessionNote: (sid, note) => req(`/api/sessions/${sid}/note`, { method: 'PUT', body: { note } }),
  addSession: (aid, body) => req(`/api/activities/${aid}/sessions`, { method: 'POST', body }),
  patchSession: (sid, body) => req(`/api/sessions/${sid}`, { method: 'PUT', body }),
  deleteSession: (sid) => req(`/api/sessions/${sid}`, { method: 'DELETE' }),
  day: (date) => req(`/api/day/${date}`),
  weekInsights: () => req('/api/insights/week'),
  saveDescription: (id, text) => req(`/api/activities/${id}/description`, { method: 'POST', body: { text } }),
  overview: () => req('/api/overview'),
  achievements: () => req('/api/achievements'),
  profile: () => req('/api/profile'),
}
