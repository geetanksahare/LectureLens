/**
 * LectureLens API client
 * Talks to the existing FastAPI backend at /api (proxied by Vite to localhost:8000)
 * Auth: Supabase JWT passed as Bearer token on every request.
 */

const BASE = '/api'

function getToken() {
  // Supabase stores the session in localStorage as sb-<project>-auth-token
  // We pull the access_token from whatever key is present.
  for (const key of Object.keys(localStorage)) {
    if (key.includes('auth-token') || key.includes('supabase')) {
      try {
        const val = JSON.parse(localStorage.getItem(key))
        const token = val?.access_token ?? val?.session?.access_token
        if (token) return token
      } catch {
        // ignore parse errors
      }
    }
  }
  return null
}

async function request(method, path, body, isFormData = false) {
  const token = getToken()
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (!isFormData && body) headers['Content-Type'] = 'application/json'

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }

  return res.json()
}

export const api = {
  health: () => request('GET', '/health'),

  // Lectures
  uploadLecture: (file, outputs) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('requested_outputs', outputs.join(','))
    return request('POST', '/lectures', fd, true)
  },
  listLectures: () => request('GET', '/lectures'),
  getLecture: (id) => request('GET', `/lectures/${id}`),

  // Quiz
  submitQuiz: (lectureId, mcqAnswers, shortAnswers = {}) =>
    request('POST', `/quiz/${lectureId}/submit`, {
      mcq_answers: mcqAnswers,
      short_answers: shortAnswers,
    }),

  // Chatbot / RAG
  askQuestion: (lectureId, question) =>
    request('POST', `/lectures/${lectureId}/ask`, { question }),
}