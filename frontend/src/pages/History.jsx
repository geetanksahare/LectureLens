import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

// SVG Icons
const PlayCircleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <polygon points="10 8 16 12 10 16 10 8"></polygon>
  </svg>
)

const EmptyStateIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400">
    <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"></path>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
    <path d="m16 19 2 2 4-4"></path>
  </svg>
)

function StatusBadge({ status }) {
  const styles = {
    done: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    queued: 'bg-gray-50 text-gray-700 border-gray-200',
    processing: 'bg-indigo-50 text-indigo-700 border-indigo-200 animate-pulse',
    failed: 'bg-red-50 text-red-700 border-red-200'
  }
  
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${styles[status] ?? styles.queued}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

export default function History() {
  const navigate = useNavigate()
  const [lectures, setLectures] = useState([])
  const [loading, setLoading]   = useState(true)
  const [search, setSearch]     = useState('')

  useEffect(() => {
    api.listLectures()
      .then(d => setLectures(d.lectures ?? []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = lectures.filter(l =>
    l.filename?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="max-w-5xl animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-1">Lecture History</h1>
          <p className="text-gray-500 font-medium">
            {lectures.length} {lectures.length === 1 ? 'lecture' : 'lectures'} in your library
          </p>
        </div>
        <button 
          className="inline-flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl font-bold text-sm shadow-sm transition-all focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600 hover:-translate-y-0.5" 
          onClick={() => navigate('/process')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>Process New</span>
        </button>
      </div>

      {/* Search */}
      {lectures.length > 0 && (
        <div className="relative mb-6">
          <svg 
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" 
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-gray-900 font-medium placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 shadow-sm transition-all"
            placeholder="Search lectures…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      )}

      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-center">
          <svg className="animate-spin h-8 w-8 text-indigo-600 mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-500 font-medium">Loading history…</p>
        </div>
      ) : lectures.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-gray-200 rounded-3xl p-12 flex flex-col items-center text-center">
          <div className="p-4 bg-gray-50 rounded-full mb-4">
            <EmptyStateIcon />
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Nothing here yet</h3>
          <p className="text-gray-500 mb-6 max-w-sm">Process your first lecture video to start building your AI-powered study library.</p>
          <button 
            className="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-6 py-2.5 rounded-xl font-bold text-sm transition-colors" 
            onClick={() => navigate('/process')}
          >
            Process a lecture
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-3xl p-12 flex flex-col items-center text-center shadow-sm">
          <div className="p-4 bg-gray-50 rounded-full mb-4">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">No results</h3>
          <p className="text-gray-500">No lectures match "{search}".</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(lec => (
            <div
              key={lec.id}
              onClick={() => lec.status === 'done' && navigate(`/history/${lec.id}`)}
              className={`group flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-5 bg-white border border-gray-200 rounded-2xl transition-all duration-200
                ${lec.status === 'done' ? 'cursor-pointer hover:border-indigo-300 hover:shadow-md hover:ring-1 hover:ring-indigo-600/10' : 'cursor-default'}
              `}
            >
              <div className="flex items-start sm:items-center flex-1 min-w-0">
                <div className={`flex-shrink-0 p-3 rounded-xl transition-colors
                  ${lec.status === 'done' ? 'bg-indigo-50 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white' : 'bg-gray-100 text-gray-500'}
                `}>
                  <PlayCircleIcon />
                </div>
                <div className="ml-4 truncate">
                  <div className={`font-bold truncate ${lec.status === 'done' ? 'text-gray-900' : 'text-gray-700'}`}>
                    {lec.filename}
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    {lec.processed_at && (
                      <span className="text-xs font-medium text-gray-500 mr-1">
                        {new Date(lec.processed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                    )}
                    {lec.requested_outputs?.map(o => (
                      <span key={o} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-[10px] font-bold uppercase tracking-wider rounded-md">
                        {o}
                      </span>
                    ))}
                  </div>
                  {lec.status === 'failed' && lec.error_message && (
                    <div className="mt-3 text-xs font-medium text-red-600 bg-red-50 px-3 py-2 rounded-lg inline-block border border-red-100">
                      {lec.error_message}
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-4 sm:mt-0 sm:ml-4 flex-shrink-0 flex items-center space-x-4 pl-14 sm:pl-0">
                <StatusBadge status={lec.status} />
                {lec.status === 'done' && (
                  <svg className="w-5 h-5 text-gray-400 group-hover:text-indigo-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}