import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './lib/AuthContext'
import Shell from './components/Shell'
import AuthPage from './pages/AuthPage'
import Dashboard from './pages/Dashboard'
import ProcessLecture from './pages/ProcessLecture'
import History from './pages/History'
import LectureDetail from './pages/LectureDetail'

function RequireAuth({ children }) {
  const { session } = useAuth()
  if (session === undefined) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-600"></div>
    </div>
  )
  if (!session) return <Navigate to="/auth" replace />
  return children
}

export default function App() {
  const { session } = useAuth()

  if (session === undefined) return null

  return (
    <Routes>
      <Route path="/auth" element={session ? <Navigate to="/" replace /> : <AuthPage />} />
      <Route element={<RequireAuth><Shell /></RequireAuth>}>
        <Route index element={<Dashboard />} />
        <Route path="process" element={<ProcessLecture />} />
        <Route path="history" element={<History />} />
        <Route path="history/:lectureId" element={<LectureDetail />} />
      </Route>
    </Routes>
  )
}