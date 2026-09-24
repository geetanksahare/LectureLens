import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { api } from '../lib/api'

// SVG Icons
const VideoIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
    <line x1="7" y1="2" x2="7" y2="22"></line>
    <line x1="17" y1="2" x2="17" y2="22"></line>
    <line x1="2" y1="12" x2="22" y2="12"></line>
    <line x1="2" y1="7" x2="7" y2="7"></line>
    <line x1="2" y1="17" x2="7" y2="17"></line>
    <line x1="17" y1="17" x2="22" y2="17"></line>
    <line x1="17" y1="7" x2="22" y2="7"></line>
  </svg>
)

const CheckCircleIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22 4 12 14.01 9 11.01"></polyline>
  </svg>
)

const ClockIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <polyline points="12 6 12 12 16 14"></polyline>
  </svg>
)

const EmptyLibraryIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-500 opacity-80">
    <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
    <path d="M6 12v5c3 3 9 3 12 0v-5"></path>
  </svg>
)

const PlayCircleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <polygon points="10 8 16 12 10 16 10 8"></polygon>
  </svg>
)

function StatusBadge({ status }) {
  const styles = {
    done: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    queued: 'bg-gray-50 text-gray-700 border-gray-200',
    processing: 'bg-amber-50 text-amber-700 border-amber-200 pulse',
    failed: 'bg-red-50 text-red-700 border-red-200'
  }
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[status] ?? styles.queued}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

function StatCard({ icon, value, label, loading, colorClass = "text-indigo-600 bg-indigo-50" }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col hover:shadow-md transition-shadow">
      <div className={`p-3 rounded-xl inline-flex w-fit mb-4 ${colorClass}`}>
        {icon}
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{loading ? '—' : value}</div>
      <div className="text-sm font-medium text-gray-500">{label}</div>
    </div>
  )
}

export default function Dashboard() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [lectures, setLectures] = useState([])
  const [loading, setLoading] = useState(true)

  const email = session?.user?.email ?? ''
  const firstName = email.split('@')[0]
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  useEffect(() => {
    api.listLectures()
      .then(d => setLectures(d.lectures ?? []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const done       = lectures.filter(l => l.status === 'done').length
  const inProgress = lectures.filter(l => l.status === 'processing' || l.status === 'queued').length

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">{greeting}, {firstName}.</h1>
          <p className="text-gray-500 mt-1">Here's an overview of your lecture library.</p>
        </div>
        <button 
          onClick={() => navigate('/process')}
          className="inline-flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg font-medium shadow-sm transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.5" opacity=".7"/>
            <path d="M5.5 4.5l4 2.5-4 2.5V4.5z" fill="currentColor"/>
          </svg>
          <span>Process Lecture</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard icon={<VideoIcon />} value={lectures.length} label="Total Lectures" loading={loading} colorClass="text-blue-600 bg-blue-50" />
        <StatCard icon={<CheckCircleIcon />} value={done} label="Processed" loading={loading} colorClass="text-emerald-600 bg-emerald-50" />
        <StatCard icon={<ClockIcon />} value={inProgress} label="In Progress" loading={loading} colorClass="text-amber-600 bg-amber-50" />
      </div>

      {/* Recent lectures */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Recent Lectures</h2>
          {lectures.length > 5 && (
            <Link to="/history" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">View all &rarr;</Link>
          )}
        </div>

        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
            <p className="text-gray-500 text-sm">Loading your library…</p>
          </div>
        ) : lectures.length === 0 ? (
          <div className="bg-white border border-gray-200 border-dashed rounded-2xl p-12 text-center flex flex-col items-center">
            <EmptyLibraryIcon />
            <h3 className="mt-4 text-lg font-bold text-gray-900">No lectures yet</h3>
            <p className="mt-1 text-gray-500 max-w-sm">Upload your first lecture video to build your AI-powered study library.</p>
            <button 
              onClick={() => navigate('/process')}
              className="mt-6 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-5 py-2.5 rounded-lg font-medium transition-colors"
            >
              Process your first lecture
            </button>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
            <ul className="divide-y divide-gray-100">
              {lectures.slice(0, 6).map(lec => (
                <li key={lec.id}>
                  <div
                    onClick={() => lec.status === 'done' && navigate(`/history/${lec.id}`)}
                    className={`block p-4 sm:p-5 hover:bg-gray-50 transition-colors ${lec.status === 'done' ? 'cursor-pointer' : 'cursor-default'}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1 min-w-0">
                        <div className="flex-shrink-0 p-3 bg-indigo-50 text-indigo-600 rounded-xl">
                          <PlayCircleIcon />
                        </div>
                        <div className="ml-4 truncate">
                          <p className="text-sm font-semibold text-gray-900 truncate">{lec.filename}</p>
                          <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                            {lec.processed_at && (
                              <span>{new Date(lec.processed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                            )}
                            {lec.requested_outputs?.length > 0 && <span>&bull;</span>}
                            <div className="flex space-x-1 overflow-hidden">
                              {lec.requested_outputs?.map(o => (
                                <span key={o} className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-600 truncate">{o}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="ml-4 flex-shrink-0 flex items-center space-x-4">
                        <StatusBadge status={lec.status} />
                        {lec.status === 'done' && (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-gray-400">
                            <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}