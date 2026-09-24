import { useState } from 'react'
import { useAuth } from '../lib/AuthContext'

function IconLens() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white">
      <circle cx="11" cy="11" r="8"></circle>
      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      <path d="M11 8a3 3 0 0 0-3 3"></path>
    </svg>
  )
}

const features = [
  { icon: '🎙️', text: 'Whisper-powered transcription with timestamps' },
  { icon: '✨', text: 'Technical & simplified summaries' },
  { icon: '🧠', text: 'Auto-generated quizzes to test your knowledge' },
  { icon: '🤖', text: 'AI tutor — ask anything about the lecture' },
]

export default function AuthPage() {
  const { signIn, signUp } = useAuth()
  const [tab, setTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function switchTab(t) { setTab(t); setError(''); setSuccess('') }

  async function handleLogin(e) {
    e.preventDefault()
    setError(''); setSuccess(''); setLoading(true)
    const { error: err } = await signIn(email, password)
    setLoading(false)
    if (err) setError(err.message)
  }

  async function handleSignUp(e) {
    e.preventDefault()
    setError(''); setSuccess('')
    if (password !== confirmPassword) { setError('Passwords do not match.'); return }
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return }
    setLoading(true)
    const { error: err } = await signUp(email, password)
    setLoading(false)
    if (err) setError(err.message)
    else setSuccess('Account created — check your email to confirm, then sign in.')
  }

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left panel */}
      <div className="hidden lg:flex lg:flex-1 lg:flex-col lg:justify-between bg-indigo-600 text-white p-12 relative overflow-hidden">
        {/* Background decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
          <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob"></div>
          <div className="absolute top-48 -right-24 w-96 h-96 bg-indigo-400 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-24 left-32 w-96 h-96 bg-indigo-700 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-4000"></div>
        </div>

        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-16">
            <IconLens />
            <span className="text-2xl font-bold tracking-tight">LectureLens</span>
          </div>

          <h1 className="text-5xl font-extrabold tracking-tight leading-[1.1] mb-6">
            Turn lectures<br />
            <span className="text-indigo-200">into knowledge.</span>
          </h1>
          <p className="text-lg text-indigo-100 max-w-md leading-relaxed mb-12">
            Upload any lecture video and get a complete study package —
            transcripts, summaries, quizzes, and an AI tutor — in minutes.
          </p>

          <div className="space-y-5">
            {features.map(f => (
              <div key={f.text} className="flex items-center space-x-4 bg-indigo-700/30 p-4 rounded-2xl backdrop-blur-sm border border-indigo-500/30">
                <div className="flex-shrink-0 w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-xl">
                  {f.icon}
                </div>
                <span className="text-indigo-50 font-medium">{f.text}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="relative z-10 text-sm text-indigo-200 font-medium">
          &copy; {new Date().getFullYear()} LectureLens. All rights reserved.
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:max-w-md animate-in slide-in-from-right-4 duration-700">
          
          {/* Mobile brand header */}
          <div className="lg:hidden flex items-center justify-center space-x-2 mb-8">
            <div className="p-2 bg-indigo-600 rounded-xl">
              <IconLens />
            </div>
            <span className="text-2xl font-bold tracking-tight text-gray-900">LectureLens</span>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
              {tab === 'login' ? 'Welcome back' : 'Create an account'}
            </h2>
            <p className="mt-2 text-sm text-gray-500 font-medium">
              {tab === 'login' ? 'Sign in to access your lecture library.' : 'Start building your AI-powered study library.'}
            </p>
          </div>

          {/* Tab switcher */}
          <div className="flex bg-gray-100 p-1 rounded-xl mb-8">
            {[['login', 'Sign in'], ['signup', 'Create account']].map(([t, label]) => (
              <button
                key={t}
                onClick={() => switchTab(t)}
                className={`flex-1 py-2.5 text-sm font-bold rounded-lg transition-all duration-200 ${
                  tab === t 
                    ? 'bg-white text-gray-900 shadow-sm ring-1 ring-black/5' 
                    : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium flex items-center">
              <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              {error}
            </div>
          )}
          
          {success && (
            <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-medium flex items-center">
              <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              {success}
            </div>
          )}

          <div className="mt-6">
            {tab === 'login' ? (
              <form onSubmit={handleLogin} className="space-y-5">
                <div>
                  <label htmlFor="email" className="block text-sm font-bold text-gray-900 mb-1">Email address</label>
                  <input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} required
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 focus:bg-white transition-all shadow-sm" 
                    placeholder="you@university.edu" />
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-bold text-gray-900 mb-1">Password</label>
                  <input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} required
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 focus:bg-white transition-all shadow-sm" 
                    placeholder="••••••••" />
                </div>
                <button type="submit" disabled={loading}
                  className="w-full flex justify-center items-center py-3.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:hover:translate-y-0 mt-8"
                >
                  {loading ? (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  ) : 'Sign in →'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleSignUp} className="space-y-5">
                <div>
                  <label htmlFor="su-email" className="block text-sm font-bold text-gray-900 mb-1">Email address</label>
                  <input id="su-email" type="email" value={email} onChange={e => setEmail(e.target.value)} required
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 focus:bg-white transition-all shadow-sm" 
                    placeholder="you@university.edu" />
                </div>
                <div>
                  <label htmlFor="su-pass" className="block text-sm font-bold text-gray-900 mb-1">Password</label>
                  <input id="su-pass" type="password" value={password} onChange={e => setPassword(e.target.value)} required
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 focus:bg-white transition-all shadow-sm" 
                    placeholder="Min. 6 characters" />
                </div>
                <div>
                  <label htmlFor="su-confirm" className="block text-sm font-bold text-gray-900 mb-1">Confirm password</label>
                  <input id="su-confirm" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 focus:bg-white transition-all shadow-sm" 
                    placeholder="••••••••" />
                </div>
                <button type="submit" disabled={loading}
                  className="w-full flex justify-center items-center py-3.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:hover:translate-y-0 mt-8"
                >
                  {loading ? (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  ) : 'Create account →'}
                </button>
              </form>
            )}
          </div>
          
          <p className="mt-8 text-center text-xs text-gray-500 font-medium">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}} />
    </div>
  )
}