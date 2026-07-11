import { CandlestickChart, Eye, EyeOff, LockKeyhole, Mail } from 'lucide-react'
import { FormEvent, useState } from 'react'

import { api } from '../lib/api'
import type { User } from '../types'

type LoginPageProps = { onLogin: (token: string, user: User) => void }

export function LoginPage({ onLogin }: LoginPageProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState(import.meta.env.DEV ? 'demo@tradeos.app' : '')
  const [password, setPassword] = useState(import.meta.env.DEV ? 'tradeos123' : '')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await api<{ access_token: string; user: User }>(mode === 'login' ? '/auth/login' : '/auth/register', {
        method: 'POST',
        body: JSON.stringify(mode === 'login' ? { email, password } : { name, email, password }),
      })
      onLogin(result.access_token, result.user)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to sign in')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-brand-panel">
        <div className="login-brand"><span className="brand-mark"><CandlestickChart size={24} /></span>TradeOS</div>
        <div className="login-copy">
          <span className="eyebrow">Your trading workspace</span>
          <h1>Clarity for every trade.</h1>
          <p>Broker data, performance analysis and trading discipline in one focused workspace.</p>
        </div>
        <div className="login-stat-row">
          <div><strong>42</strong><span>Synced trades</span></div>
          <div><strong>68%</strong><span>Win rate</span></div>
          <div><strong>1.82</strong><span>Profit factor</span></div>
        </div>
      </section>
      <section className="login-form-wrap">
        <form className="login-form" onSubmit={submit}>
          <div className="login-form-heading"><h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2><p>{mode === 'login' ? 'Sign in to your TradeOS workspace' : 'Start your TradeOS workspace'}</p></div>
          {mode === 'register' && <label>Full name<div className="input-with-icon"><input value={name} onChange={(event) => setName(event.target.value)} minLength={2} required /></div></label>}
          <label>Email address<div className="input-with-icon"><Mail size={17} /><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></div></label>
          <label>Password<div className="input-with-icon"><LockKeyhole size={17} /><input type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} required /><button type="button" onClick={() => setShowPassword((value) => !value)} title={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
          {error && <div className="form-error">{error}</div>}
          <button className="primary-button login-button" disabled={loading}>{loading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}</button>
          <button type="button" className="auth-switch" onClick={() => { setMode((value) => value === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Create a new account' : 'Already have an account? Sign in'}</button>
          {import.meta.env.DEV && <div className="demo-credentials"><span>Demo account</span><code>demo@tradeos.app</code><code>tradeos123</code></div>}
        </form>
      </section>
    </main>
  )
}
