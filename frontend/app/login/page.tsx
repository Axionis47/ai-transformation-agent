'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password')
      return
    }
    setLoading(true)
    setError(null)
    // TODO: Wire to Firebase Auth
    // For now, simulate auth and redirect
    await new Promise(r => setTimeout(r, 400))
    router.push('/')
  }

  return (
    <div className="min-h-screen bg-canvas flex">
      {/* Left: Branding panel */}
      <div className="hidden lg:flex lg:w-[45%] bg-[#0a0a0a] flex-col justify-between p-12">
        <div>
          <h1 className="text-3xl font-semibold text-white tracking-tight">AI Opportunity Mapper</h1>
          <p className="text-sm text-white/40 mt-1 font-mono">Evidence-backed AI discovery</p>
        </div>
        <div className="space-y-6">
          <p className="text-lg text-white/80 leading-relaxed max-w-md">
            Multi-agent research. Hypothesis-driven analysis. Every recommendation traced to its source.
          </p>
          <div className="flex items-center gap-6 text-white/30 text-2xs font-mono uppercase tracking-wider">
            <span>Research</span>
            <span className="w-4 border-t border-white/20" />
            <span>Hypothesize</span>
            <span className="w-4 border-t border-white/20" />
            <span>Validate</span>
          </div>
        </div>
        <p className="text-2xs text-white/20 font-mono">&copy; {new Date().getFullYear()}</p>
      </div>

      {/* Right: Login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          {/* Mobile branding */}
          <div className="lg:hidden mb-10">
            <h1 className="text-2xl font-semibold text-ink tracking-tight">AI Opportunity Mapper</h1>
            <p className="text-sm text-ink-tertiary mt-1 font-mono">Evidence-backed AI discovery</p>
          </div>

          <div className="mb-8">
            <h2 className="text-lg font-semibold text-ink">Sign in</h2>
            <p className="text-sm text-ink-secondary mt-1">Access your analysis workspace</p>
          </div>

          {error && (
            <div className="bg-rose/8 border border-rose/20 rounded-md p-3 mb-6">
              <p className="text-sm text-rose">{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs text-ink-secondary uppercase tracking-wider font-medium mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="analyst@company.com"
                className="w-full bg-canvas-raised border border-edge-subtle rounded-md px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-tertiary/50 focus:outline-none focus:border-mint focus:ring-1 focus:ring-mint/30 transition-colors"
                autoComplete="email"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs text-ink-secondary uppercase tracking-wider font-medium mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-canvas-raised border border-edge-subtle rounded-md px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-tertiary/50 focus:outline-none focus:border-mint focus:ring-1 focus:ring-mint/30 transition-colors"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-mint text-ink-inverse py-2.5 text-sm font-semibold rounded-md disabled:opacity-40 hover:bg-mint-bright transition-colors mt-2"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="text-2xs text-ink-tertiary text-center mt-8 font-mono">
            AI Opportunity Mapper v1.0
          </p>
        </div>
      </div>
    </div>
  )
}
