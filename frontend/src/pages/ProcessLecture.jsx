import { useState, useRef, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

// SVG Icons
const TranscriptIcon = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>;
const SubtitlesIcon = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>;
const SummaryIcon = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>;
const QuizIcon = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>;
const GlossaryIcon = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>;
const PlayCircleIcon = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>;
const CheckCircleIcon = () => <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>;
const UploadIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-500">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="17 8 12 3 7 8"></polyline>
    <line x1="12" y1="3" x2="12" y2="15"></line>
  </svg>
)

const ACCEPTED = '.mp4,.mkv,.mov,.avi,.webm'

const OUTPUT_OPTIONS = [
  { id: 'transcript', icon: <TranscriptIcon />, label: 'Transcript',  desc: 'Timestamped text via Whisper' },
  { id: 'subtitles',  icon: <SubtitlesIcon />,  label: 'Subtitles',   desc: 'SRT + VTT caption files' },
  { id: 'summary',    icon: <SummaryIcon />,    label: 'Summary',     desc: 'Technical + simplified summaries' },
  { id: 'quiz',       icon: <QuizIcon />,       label: 'Quiz',        desc: '10 auto-generated MCQs' },
  { id: 'glossary',   icon: <GlossaryIcon />,   label: 'Glossary',    desc: 'Key terms extracted' },
]

const STEPS = {
  queued:     { label: 'Queued — waiting to start', pct: 8 },
  processing: { label: 'Pipeline running…',         pct: 55 },
  done:       { label: 'Complete',                  pct: 100 },
  failed:     { label: 'Processing failed',         pct: 100 },
}

export default function ProcessLecture() {
  const navigate = useNavigate()
  const fileRef  = useRef(null)
  const pollRef  = useRef(null)

  const [file, setFile]           = useState(null)
  const [dragOver, setDragOver]   = useState(false)
  const [outputs, setOutputs]     = useState(['transcript', 'subtitles', 'summary', 'quiz'])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [job, setJob]             = useState(null)
  const [pollStatus, setPollStatus] = useState(null)

  const startPolling = useCallback((id) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const d = await api.getLecture(id)
        setPollStatus(d.status)
        if (d.status === 'done' || d.status === 'failed') clearInterval(pollRef.current)
      } catch {}
    }, 3000)
  }, [])

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  function toggleOutput(id) {
    setOutputs(p => p.includes(id) ? p.filter(o => o !== id) : [...p, id])
  }

  function handleDrop(e) {
    e.preventDefault(); setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  async function handleSubmit() {
    if (!file)             { setUploadError('Please select a video file.'); return }
    if (!outputs.length)   { setUploadError('Select at least one output type.'); return }
    setUploadError(''); setUploading(true)
    try {
      const result = await api.uploadLecture(file, outputs)
      setJob(result)
      setPollStatus(result.status)
      if (result.status !== 'done') startPolling(result.lecture_id)
    } catch (err) {
      setUploadError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const effectiveStatus = pollStatus ?? job?.status
  const step   = STEPS[effectiveStatus]
  const isDone = effectiveStatus === 'done'
  const isFailed = effectiveStatus === 'failed'

  return (
    <div className="max-w-4xl animate-in fade-in duration-500">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">Process a Lecture</h1>
        <p className="text-gray-500">Upload a video file and the AI pipeline handles everything.</p>
      </div>

      {!job ? (
        <>
          {/* Upload zone */}
          <div
            className={`relative border-2 border-dashed rounded-3xl p-12 mb-8 text-center flex flex-col items-center justify-center transition-all duration-200 cursor-pointer 
              ${dragOver ? 'border-indigo-500 bg-indigo-50/50 scale-[1.02]' : 'border-gray-300 bg-white hover:border-indigo-400 hover:bg-gray-50'}
              ${file ? 'border-emerald-400 bg-emerald-50/30 hover:border-emerald-500 hover:bg-emerald-50/50' : ''}
            `}
            onClick={() => fileRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <input ref={fileRef} type="file" accept={ACCEPTED} className="hidden"
              onChange={e => setFile(e.target.files[0] ?? null)} />
            
            <div className={`p-4 rounded-full mb-4 ${file ? 'bg-emerald-100' : 'bg-indigo-100'}`}>
              {file ? <CheckCircleIcon /> : <UploadIcon />}
            </div>
            
            {file ? (
              <>
                <h3 className="text-xl font-bold text-gray-900 mb-1">{file.name}</h3>
                <p className="text-sm font-medium text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(1)} MB · Click to change file
                </p>
              </>
            ) : (
              <>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Drag & drop your lecture video</h3>
                <p className="text-sm text-gray-500 font-medium">or click to browse your files</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2 text-xs font-medium text-gray-400">
                  <span className="px-2 py-1 bg-gray-100 rounded-md">MP4</span>
                  <span className="px-2 py-1 bg-gray-100 rounded-md">MKV</span>
                  <span className="px-2 py-1 bg-gray-100 rounded-md">MOV</span>
                  <span className="px-2 py-1 bg-gray-100 rounded-md">AVI</span>
                  <span className="px-2 py-1 bg-gray-100 rounded-md">WebM</span>
                </div>
              </>
            )}
          </div>

          {/* Output selector */}
          <div className="mb-8">
            <div className="mb-4">
              <h3 className="text-lg font-bold text-gray-900 mb-1">Choose outputs</h3>
              <p className="text-sm text-gray-500">Select what you want the AI pipeline to generate.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {OUTPUT_OPTIONS.map(opt => {
                const sel = outputs.includes(opt.id)
                return (
                  <label key={opt.id} 
                    className={`relative flex items-start p-4 cursor-pointer rounded-2xl border-2 transition-all duration-200
                      ${sel ? 'border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-600 shadow-sm' : 'border-gray-200 bg-white hover:border-indigo-300 hover:bg-gray-50'}
                    `}
                    onClick={() => toggleOutput(opt.id)}>
                    <input type="checkbox" className="hidden" checked={sel} onChange={() => toggleOutput(opt.id)} />
                    
                    <div className={`flex-shrink-0 p-2.5 rounded-xl mr-4 ${sel ? 'bg-indigo-600 text-white shadow-sm' : 'bg-gray-100 text-gray-500'}`}>
                      {opt.icon}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-bold truncate ${sel ? 'text-indigo-900' : 'text-gray-900'}`}>{opt.label}</div>
                      <div className={`text-xs mt-1 leading-relaxed ${sel ? 'text-indigo-700/80' : 'text-gray-500'}`}>{opt.desc}</div>
                    </div>
                    
                    <div className={`absolute top-4 right-4 h-5 w-5 rounded-full border flex items-center justify-center transition-colors
                      ${sel ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300'}
                    `}>
                      {sel && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>}
                    </div>
                  </label>
                ) 
              })}
            </div>
          </div>

          {uploadError && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium mb-8 flex items-center">
              <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              {uploadError}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-4 border-t border-gray-200 pt-6">
            <button 
              disabled={uploading || !file} 
              onClick={handleSubmit}
              className={`inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-bold text-sm shadow-sm transition-all focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600
                ${uploading || !file 
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white hover:shadow-md hover:-translate-y-0.5'}
              `}
            >
              {uploading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Uploading…</span>
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                  <span>Start Processing</span>
                </>
              )}
            </button>
            {file && !uploading && (
              <button 
                className="px-6 py-3 rounded-xl font-bold text-sm text-gray-600 hover:bg-gray-100 transition-colors" 
                onClick={() => setFile(null)}
              >
                Clear
              </button>
            )}
          </div>
        </>
      ) : (
        /* Job progress */
        <div className="bg-white border border-gray-200 rounded-3xl p-8 max-w-2xl mx-auto shadow-sm">
          {job.duplicate && (
            <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm font-medium mb-6 flex items-start">
              <svg className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              <span>This video was already processed. Returning cached results immediately.</span>
            </div>
          )}

          <div className="flex items-center space-x-4 mb-8">
            <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl flex-shrink-0">
              <PlayCircleIcon />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-bold text-gray-900 truncate">{file?.name ?? 'Lecture'}</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {outputs.map(o => (
                  <span key={o} className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-600">
                    {o}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="mb-2 flex items-center justify-between">
            <span className={`text-sm font-bold ${isFailed ? 'text-red-600' : isDone ? 'text-emerald-600' : 'text-gray-900'}`}>
              {step?.label ?? effectiveStatus}
            </span>
            <span className="text-sm font-bold text-gray-400">{step?.pct ?? 10}%</span>
          </div>

          <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden mb-6">
            <div 
              className={`h-full rounded-full transition-all duration-500 ease-out ${
                isFailed ? 'bg-red-500' : isDone ? 'bg-emerald-500' : 'bg-indigo-600'
              } ${!isDone && !isFailed ? 'relative overflow-hidden' : ''}`} 
              style={{ width: `${step?.pct ?? 10}%` }}
            >
              {!isDone && !isFailed && (
                <div className="absolute inset-0 bg-white/20" style={{ animation: 'shimmer 1.5s infinite linear', transform: 'skewX(-20deg)' }}></div>
              )}
            </div>
          </div>

          {!isDone && !isFailed && (
            <p className="text-sm text-gray-500 font-medium animate-pulse text-center">Processing may take a few minutes depending on lecture length…</p>
          )}

          {isFailed && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
              Processing failed. Check the backend logs for details.
            </div>
          )}

          {isDone && (
            <div className="flex flex-wrap gap-3 mt-8 pt-6 border-t border-gray-100">
              <button 
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl font-bold text-sm shadow-sm transition-colors"
                onClick={() => navigate(`/history/${job.lecture_id}`)}
              >
                View Results &rarr;
              </button>
              <button 
                className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-6 py-2.5 rounded-xl font-bold text-sm transition-colors"
                onClick={() => { setJob(null); setFile(null); setPollStatus(null) }}
              >
                Process Another
              </button>
            </div>
          )}
        </div>
      )}
      
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes shimmer {
          100% { transform: translateX(200%) skewX(-20deg); }
          0% { transform: translateX(-200%) skewX(-20deg); }
        }
      `}} />
    </div>
  )
}