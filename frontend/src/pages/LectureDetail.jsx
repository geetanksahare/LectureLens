import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../lib/api'

// ── Helpers ──────────────────────────────────────────────────────
function mmss(sec) {
  const m = Math.floor(sec / 60), s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

async function downloadAsFile(url, filename) {
  const res = await fetch(url)
  const blob = await res.blob()
  const blobUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(blobUrl)
}

// ── Sub-components ────────────────────────────────────────────────
function TranscriptTab({ url }) {
  const [segments, setSegments] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!url) { setErr('No transcript available for this lecture.'); return }
    fetch(url)
      .then(r => r.json())
      .then(d => setSegments(d.segments ?? []))
      .catch(() => setErr('Could not load transcript.'))
  }, [url])

  if (err) return <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm">{err}</div>
  if (!segments) return <div className="animate-pulse text-gray-500 font-medium p-4">Loading transcript…</div>
  if (segments.length === 0) return <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-700 text-sm">No segments found.</div>

  return (
    <div className="space-y-1">
      {segments.map((seg, i) => (
        <div key={i} className="group flex p-2 rounded-lg hover:bg-gray-50 transition-colors">
          <span className="w-16 flex-shrink-0 text-xs font-mono font-medium text-indigo-500 pt-1 group-hover:text-indigo-600 transition-colors">
            {mmss(seg.start ?? 0)}
          </span>
          <span className="flex-1 text-gray-800 text-base leading-relaxed">{seg.text}</span>
        </div>
      ))}
    </div>
  )
}

function SummaryTab({ url }) {
  const [data, setData] = useState(null)
  const [mode, setMode] = useState('simple') // 'simple' | 'technical'
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!url) { setErr('No summary available for this lecture.'); return }
    fetch(url)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => setErr('Could not load summary.'))
  }, [url])

  if (err) return <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm">{err}</div>
  if (!data) return <div className="animate-pulse text-gray-500 font-medium p-4">Loading summary…</div>

  const chunks = data.chunks ?? []

  // Merge all chunks into one continuous summary for display,
  // even though they're generated/stored chunk-by-chunk in the background.
  const fullText = chunks
    .map(chunk => (mode === 'simple' ? (chunk.simple_summary ?? chunk.summary ?? '') : (chunk.technical_summary ?? chunk.summary ?? '')))
    .filter(Boolean)
    .join('\n\n')

  return (
    <div>
      <div className="flex bg-gray-100 p-1 rounded-xl w-fit mb-8">
        <button 
          className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${mode === 'simple' ? 'bg-white text-indigo-700 shadow-sm ring-1 ring-black/5' : 'text-gray-600 hover:text-gray-900'}`} 
          onClick={() => setMode('simple')}
        >
          Simple
        </button>
        <button 
          className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${mode === 'technical' ? 'bg-white text-indigo-700 shadow-sm ring-1 ring-black/5' : 'text-gray-600 hover:text-gray-900'}`} 
          onClick={() => setMode('technical')}
        >
          Technical
        </button>
      </div>

      {chunks.length === 0 ? (
        <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-700 text-sm">No summary found.</div>
      ) : (
        <div className="bg-white border border-gray-200 p-8 rounded-2xl shadow-sm">
          <p className="text-gray-800 text-base leading-relaxed whitespace-pre-wrap text-justify">
            {fullText}
          </p>
        </div>
      )}
    </div>
  )
}


function GlossaryTab({ url }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!url) { setErr('No glossary available for this lecture.'); return }
    fetch(url)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => setErr('Could not load glossary.'))
  }, [url])

  if (err) return <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm">{err}</div>
  if (!data) return <div className="animate-pulse text-gray-500 font-medium p-4">Loading glossary…</div>

  const terms = data.glossary ?? []

  if (terms.length === 0) return <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-700 text-sm">No glossary terms found for this lecture.</div>

  return (
    <div className="space-y-3">
      {terms.map((t, i) => (
        <div key={i} className="bg-white border border-gray-200 p-5 rounded-2xl shadow-sm flex items-start gap-4">
          {t.timestamp !== undefined && (
            <div className="text-xs font-mono font-bold text-indigo-500 bg-indigo-50 px-2.5 py-1 rounded-md flex-shrink-0 mt-0.5">
              {mmss(t.timestamp)}
            </div>
          )}
          <div>
            <div className="text-base font-bold text-gray-900">{t.term}</div>
            <div className="text-sm text-gray-600 mt-1 leading-relaxed">{t.definition}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function QuizTab({ lectureId, url }) {
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})       // MCQ: questionText → chosenKey
  const [shortAnswers, setShortAnswers] = useState({}) // Short answer: questionText → typed text
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!url) { setErr('No quiz generated for this lecture.'); return }
    fetch(url)
      .then(r => r.json())
      .then(d => setQuiz(d))
      .catch(() => setErr('Could not load quiz.'))
  }, [url])

  if (err) return <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm">{err}</div>
  if (!quiz) return <div className="animate-pulse text-gray-500 font-medium p-4">Loading quiz…</div>

  const allMcqs = (quiz.quiz ?? []).flatMap(section => section.mcqs ?? [])
  const allShortAnswers = (quiz.quiz ?? []).flatMap(section => section.short_answers ?? [])
  const totalQuestions = allMcqs.length + allShortAnswers.length

  if (totalQuestions === 0) return <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-700 text-sm">No questions found in this quiz.</div>

  const answeredCount = Object.keys(answers).length + Object.values(shortAnswers).filter(v => v.trim() !== '').length

  async function handleSubmit() {
    setSubmitting(true); setErr('')
    try {
      const mcqAnswers = {}
      allMcqs.forEach(q => { if (answers[q.question]) mcqAnswers[q.question] = answers[q.question] })
      const shortAnswerPayload = {}
      allShortAnswers.forEach(q => { if (shortAnswers[q.question]) shortAnswerPayload[q.question] = shortAnswers[q.question] })
      const res = await api.submitQuiz(lectureId, mcqAnswers, shortAnswerPayload)
      setResult(res)
    } catch (e) {
      setErr(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const resultMap = {}
  if (result) {
    ;(result.results ?? []).forEach(r => { resultMap[r.question] = r })
  }

  const pct = result ? Math.round((result.score / result.total_questions) * 100) : null

  return (
    <div className="max-w-3xl">
      {result && (
        <div className={`p-6 rounded-2xl border-2 mb-8 flex items-center shadow-sm ${pct >= 70 ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
          <div className="text-4xl mr-4">{pct >= 70 ? '🎉' : '📚'}</div>
          <div>
            <div className="font-bold text-lg mb-1">Quiz Completed!</div>
            <div className="text-sm font-medium">You scored {result.score} out of {result.total_questions} ({pct}%).</div>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {allMcqs.map((q, idx) => {
          const chosen = answers[q.question]
          const res = resultMap[q.question]
          const opts = q.options ?? {}

          return (
            <div key={`mcq-${idx}`} className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <h4 className="text-lg font-bold text-gray-900 mb-4 flex">
                <span className="text-indigo-500 mr-2">{idx + 1}.</span> {q.question}
              </h4>
              <div className="space-y-3">
                {Object.entries(opts).map(([key, text]) => {
                  let borderClass = 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                  let textClass = 'text-gray-700'
                  let markerClass = 'bg-gray-100 text-gray-600'

                  if (result && res) {
                    if (key === res.correct_answer) {
                      borderClass = 'border-emerald-500 bg-emerald-50/50 ring-1 ring-emerald-500'
                      textClass = 'text-emerald-900 font-medium'
                      markerClass = 'bg-emerald-500 text-white'
                    } else if (key === chosen && key !== res.correct_answer) {
                      borderClass = 'border-red-300 bg-red-50/50'
                      textClass = 'text-red-900'
                      markerClass = 'bg-red-400 text-white'
                    } else {
                      borderClass = 'border-gray-100 bg-gray-50 opacity-60'
                    }
                  } else if (chosen === key) {
                    borderClass = 'border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-600'
                    textClass = 'text-indigo-900 font-medium'
                    markerClass = 'bg-indigo-600 text-white'
                  }

                  return (
                    <label key={key} className={`relative flex items-center p-4 cursor-pointer rounded-xl border-2 transition-all ${borderClass} ${result ? 'cursor-default' : ''}`}>
                      <input
                        type="radio"
                        name={`q-${idx}`}
                        value={key}
                        checked={chosen === key}
                        disabled={!!result}
                        onChange={() => setAnswers(prev => ({ ...prev, [q.question]: key }))}
                        className="hidden"
                      />
                      <span className={`flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-sm font-bold mr-4 transition-colors ${markerClass}`}>
                        {key}
                      </span>
                      <span className={`text-base leading-snug ${textClass}`}>{text}</span>

                      {result && res && key === res.correct_answer && (
                        <svg className="absolute right-4 w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                      )}
                      {result && res && key === chosen && key !== res.correct_answer && (
                        <svg className="absolute right-4 w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                      )}
                    </label>
                  )
                })}
              </div>
              {result && res?.explanation && (
                <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-700 leading-relaxed">
                  <span className="font-bold text-gray-900 mr-2">💡 Explanation:</span>
                  {res.explanation}
                </div>
              )}
            </div>
          )
        })}

        {allShortAnswers.map((q, idx) => {
          const typed = shortAnswers[q.question] || ''
          const res = resultMap[q.question]

          return (
            <div key={`sa-${idx}`} className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <h4 className="text-lg font-bold text-gray-900 mb-4 flex">
                <span className="text-indigo-500 mr-2">{allMcqs.length + idx + 1}.</span> {q.question}
              </h4>

              {!result ? (
                <textarea
                  className="w-full p-4 rounded-xl border-2 border-gray-200 focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 outline-none text-base"
                  rows={3}
                  placeholder="Type your answer…"
                  value={typed}
                  onChange={(e) => setShortAnswers(prev => ({ ...prev, [q.question]: e.target.value }))}
                />
              ) : (
                <div className="space-y-3">
                  <div className={`p-4 rounded-xl border-2 ${res?.is_correct ? 'border-emerald-500 bg-emerald-50/50' : 'border-red-300 bg-red-50/50'}`}>
                    <div className="text-xs font-bold uppercase text-gray-500 mb-1">Your answer</div>
                    <div className="text-base">{res?.your_answer || <span className="italic text-gray-400">No answer given</span>}</div>
                  </div>
                  <div className="p-4 rounded-xl border-2 border-emerald-500 bg-emerald-50/50">
                    <div className="text-xs font-bold uppercase text-gray-500 mb-1">Model answer</div>
                    <div className="text-base">{res?.model_answer}</div>
                  </div>
                  {res?.feedback && (
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-700 leading-relaxed">
                      <span className="font-bold text-gray-900 mr-2">💡 Feedback:</span>
                      {res.feedback}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {err && <div className="mt-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium">{err}</div>}

      {!result ? (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <button
            className={`inline-flex items-center justify-center w-full sm:w-auto px-8 py-3.5 rounded-xl font-bold text-sm transition-all focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600
              ${submitting || answeredCount < totalQuestions
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm hover:shadow-md hover:-translate-y-0.5'
              }
            `}
            disabled={submitting || answeredCount < totalQuestions}
            onClick={handleSubmit}
          >
            {submitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Submitting…</span>
              </>
            ) : (
              `Submit quiz (${answeredCount}/${totalQuestions} answered)`
            )}
          </button>
        </div>
      ) : null}
    </div>
  )
}

function SubtitlesTab({ srtUrl, vttUrl, filename }) {
  const [downloading, setDownloading] = useState(null) // 'srt' | 'vtt' | null

  if (!srtUrl && !vttUrl) return <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-700 text-sm">No subtitle files available for this lecture.</div>

  const baseName = (filename ?? 'lecture').replace(/\.[^/.]+$/, '')

  async function handleDownload(kind, url, ext) {
    setDownloading(kind)
    try {
      await downloadAsFile(url, `${baseName}.${ext}`)
    } catch (e) {
      alert('Failed to download file: ' + e.message)
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div className="max-w-2xl bg-white border border-gray-200 p-8 rounded-2xl shadow-sm text-center">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto text-indigo-400 mb-4">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <h3 className="text-lg font-bold text-gray-900 mb-2">Download Captions</h3>
      <p className="text-gray-500 mb-8 max-w-sm mx-auto">Download caption files to use with your preferred local video player like VLC or QuickTime.</p>
      
      <div className="flex flex-wrap items-center justify-center gap-4">
        {srtUrl && (
          <button
            disabled={downloading === 'srt'}
            onClick={() => handleDownload('srt', srtUrl, 'srt')}
            className="inline-flex items-center px-6 py-3 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl font-bold text-sm transition-colors disabled:opacity-50"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            {downloading === 'srt' ? 'Downloading…' : 'Download .srt'}
          </button>
        )}
        {vttUrl && (
          <button
            disabled={downloading === 'vtt'}
            onClick={() => handleDownload('vtt', vttUrl, 'vtt')}
            className="inline-flex items-center px-6 py-3 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl font-bold text-sm transition-colors disabled:opacity-50"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            {downloading === 'vtt' ? 'Downloading…' : 'Download .vtt'}
          </button>
        )}
      </div>
    </div>
  )
}

function ChatTab({ lectureId }) {
  const [messages, setMessages] = useState([]) // { role: 'user'|'assistant', text, timestamps }
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function send() {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await api.askQuestion(lectureId, q)
      setMessages(prev => [...prev, { role: 'assistant', text: res.answer, timestamps: res.timestamps }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: `Error: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }

  return (
    <div className="flex flex-col h-[600px] max-w-4xl bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="bg-gray-50 border-b border-gray-200 p-4">
        <h3 className="font-bold text-gray-900 flex items-center">
          <BotIcon className="mr-2 text-indigo-600" /> AI Assistant
        </h3>
        <p className="text-xs font-medium text-gray-500 mt-1">Powered by vector search over the lecture transcript.</p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-gray-50/50">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-gray-400">
            <BotIcon className="w-12 h-12 mb-3 text-gray-300" />
            <p className="font-medium">No messages yet. Ask a question below!</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed
              ${m.role === 'user' 
                ? 'bg-indigo-600 text-white rounded-br-none' 
                : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none'
              }
            `}>
              <div className="whitespace-pre-wrap">{m.text}</div>
              {m.timestamps?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-2">
                  <span className="text-xs font-semibold text-gray-400">Sources:</span>
                  {m.timestamps.map(t => (
                    <span key={t} className="text-xs font-mono bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded-md">
                      {mmss(t)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-none px-5 py-4 shadow-sm flex space-x-1.5">
              <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      
      <div className="p-4 bg-white border-t border-gray-200">
        <div className="relative flex items-center">
          <input
            type="text"
            className="w-full pl-4 pr-14 py-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 font-medium placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 focus:bg-white transition-all shadow-sm"
            placeholder="Ask a question..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button 
            className="absolute right-2 p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50 disabled:hover:bg-transparent"
            onClick={send} 
            disabled={!input.trim() || loading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────
const TranscriptIcon = ({ className }) => <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>;
const SubtitlesIcon = ({ className }) => <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>;
const SummaryIcon = ({ className }) => <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>;
const QuizIcon = ({ className }) => <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>;
const BotIcon = ({ className }) => <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>;


function GlossaryIcon(props) {
  return <svg {...props} className={`w-5 h-5 ${props.className ?? ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
}


const TABS = [
  { id: 'transcript', label: 'Transcript', icon: TranscriptIcon },
  { id: 'summary',    label: 'Summary',    icon: SummaryIcon },
  { id: 'glossary',   label: 'Glossary',   icon: GlossaryIcon },
  { id: 'quiz',       label: 'Quiz',       icon: QuizIcon },
  { id: 'subtitles',  label: 'Subtitles',  icon: SubtitlesIcon },
  { id: 'chat',       label: 'Ask AI',     icon: BotIcon },
]

export default function LectureDetail() {
  const { lectureId } = useParams()
  const [lecture, setLecture] = useState(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [activeTab, setActiveTab] = useState('transcript')

  useEffect(() => {
    api.getLecture(lectureId)
      .then(setLecture)
      .catch(e => setErr(e.message))
      .finally(() => setLoading(false))
  }, [lectureId])

  // Compute these safely even before `lecture` has loaded
  const outputs = lecture?.outputs ?? {}
  const available = new Set(Object.keys(outputs))

  const visibleTabs = TABS.filter(t => {
    if (t.id === 'transcript') return available.has('transcript')
    if (t.id === 'summary')    return available.has('summary')
    if (t.id === 'glossary')   return available.has('glossary')
    if (t.id === 'quiz')       return available.has('quiz')
    if (t.id === 'subtitles')  return available.has('subtitles_srt') || available.has('subtitles_vtt')
    if (t.id === 'chat')       return true
    return false
  })

  // Ensure active tab is visible, otherwise default to first available
  // (Moved above the early returns so this hook ALWAYS runs, every render)
  useEffect(() => {
    if (visibleTabs.length > 0 && !visibleTabs.find(t => t.id === activeTab)) {
      setActiveTab(visibleTabs[0].id)
    }
  }, [visibleTabs, activeTab])

  if (loading) return (
    <div className="py-20 flex flex-col items-center justify-center text-center">
      <svg className="animate-spin h-8 w-8 text-indigo-600 mb-4" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p className="text-gray-500 font-medium">Loading lecture details…</p>
    </div>
  )

  if (err) return <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium">{err}</div>
  if (!lecture) return null

  return (
    <div className="max-w-5xl animate-in fade-in duration-500">
      <Link 
        to="/history" 
        className="inline-flex items-center text-sm font-bold text-gray-500 hover:text-indigo-600 transition-colors mb-6"
      >
        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        Back to History
      </Link>
      
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">{lecture.filename}</h1>
        <p className="text-gray-500 font-medium text-sm flex items-center">
          <svg className="w-4 h-4 mr-1.5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          {lecture.processed_at ? new Date(lecture.processed_at).toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short' }) : 'Unknown date'}
        </p>
      </div>

      <div className="border-b border-gray-200 mb-8 overflow-x-auto hide-scrollbar">
        <div className="flex space-x-1 min-w-max pb-px">
          {visibleTabs.map(t => {
            const isActive = activeTab === t.id
            const Icon = t.icon
            return (
              <button 
                key={t.id} 
                className={`flex items-center space-x-2 px-5 py-3.5 border-b-2 text-sm font-bold transition-colors whitespace-nowrap
                  ${isActive 
                    ? 'border-indigo-600 text-indigo-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
                onClick={() => setActiveTab(t.id)}
              >
                <Icon className={isActive ? 'text-indigo-600' : 'text-gray-400'} />
                <span>{t.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="pb-12">
        {activeTab === 'transcript' && <TranscriptTab url={outputs.transcript?.url} />}
        {activeTab === 'summary'    && <SummaryTab url={outputs.summary?.url} />}
        {activeTab === 'glossary'   && <GlossaryTab url={outputs.glossary?.url} />}
        {activeTab === 'quiz'       && <QuizTab lectureId={lectureId} url={outputs.quiz?.url} />}
        {activeTab === 'subtitles'  && <SubtitlesTab srtUrl={outputs.subtitles_srt?.url} vttUrl={outputs.subtitles_vtt?.url} filename={lecture.filename} />}
        {activeTab === 'chat'       && <ChatTab lectureId={lectureId} />}
      </div>
    </div>
  )
}