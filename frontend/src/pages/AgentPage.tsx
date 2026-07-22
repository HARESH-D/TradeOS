import {
  BookOpenCheck,
  Bot,
  CheckCircle2,
  Cloud,
  Database,
  Globe2,
  Laptop,
  Plus,
  Search,
  Send,
  ShieldCheck,
} from 'lucide-react'
import { FormEvent, useCallback, useEffect, useState } from 'react'

import { api } from '../lib/api'
import { formatDateTime } from '../lib/format'
import type { AgentRun, AgentRuntimeStatus } from '../types'

type AgentMode = 'research' | 'trades' | 'portfolio'
type AgentProvider = 'gemini' | 'llama'

const suggestions: Record<AgentMode, string[]> = {
  research: [
    'Research a company and build an evidence-backed briefing',
    'Compare two sectors using recent primary sources',
  ],
  trades: [
    'Review my imported trades for recurring behavioral patterns',
    'Identify the largest evidence-backed performance risk in my closed trades',
  ],
  portfolio: [
    'Compare portfolio performance across symbols and outcomes',
    'Review concentration and performance using my current portfolio snapshot',
  ],
}

export function AgentPage() {
  const [mode, setMode] = useState<AgentMode>('research')
  const [provider, setProvider] = useState<AgentProvider>('gemini')
  const [prompt, setPrompt] = useState('')
  const [runtime, setRuntime] = useState<AgentRuntimeStatus | null>(null)
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [activeRun, setActiveRun] = useState<AgentRun | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    const [status, history] = await Promise.all([
      api<AgentRuntimeStatus>('/agent/status'),
      api<AgentRun[]>('/agent/runs'),
    ])
    setRuntime(status)
    setRuns(history)
    setActiveRun((current) => current ?? history[0] ?? null)
  }, [])

  useEffect(() => { void load().catch((reason) => setError(reason.message)) }, [load])

  const providerRuntime = runtime?.providers[provider]
  const providerReady = providerRuntime?.configured ?? false
  const modeReady = (providerRuntime?.modes.includes(mode) ?? false) && (runtime?.modes[mode] ?? false)
  const canRun = providerReady && modeReady && prompt.trim().length >= 5 && !busy

  function selectProvider(nextProvider: AgentProvider) {
    setProvider(nextProvider)
    const supportedModes = runtime?.providers[nextProvider].modes ?? (nextProvider === 'gemini' ? ['research'] : ['trades', 'portfolio'])
    if (!supportedModes.includes(mode)) setMode(supportedModes[0])
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!canRun) return
    setBusy(true); setError('')
    try {
      const run = await api<AgentRun>('/agent/runs', {
        method: 'POST',
        body: JSON.stringify({ mode, provider, prompt: prompt.trim() }),
      })
      setRuns((current) => [run, ...current.filter((item) => item.id !== run.id)])
      setActiveRun(run)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Research run failed')
      await load().catch(() => undefined)
    } finally {
      setBusy(false)
    }
  }

  function newTask() {
    setActiveRun(null)
    setPrompt('')
    setError('')
  }

  return (
    <div className="agent-page">
      <aside className="agent-rail panel">
        <button className="primary-button agent-new-task" onClick={newTask}>
          <Plus size={16} /> New task
        </button>

        <div className="agent-rail-section">
          <span className="agent-section-label">Agent runs</span>
          {runs.length === 0 && <div className="agent-run-empty"><BookOpenCheck size={18} /><span>No runs yet</span></div>}
          <div className="agent-run-list">
            {runs.map((run) => (
              <button key={run.id} className={activeRun?.id === run.id ? 'active' : ''} onClick={() => setActiveRun(run)}>
                <span>{run.prompt}</span><small>{formatDateTime(run.completed_at ?? run.created_at)}</small><i className={run.status} />
              </button>
            ))}
          </div>
        </div>

        <div className="agent-rail-section runtime-section">
          <span className="agent-section-label">Runtime</span>
          <div className="runtime-row"><Cloud size={16} /><div><strong>Gemini API</strong><span>{runtime?.providers.gemini.configured ? runtime.providers.gemini.model : 'Not configured'}</span></div><i className={runtime?.providers.gemini.configured ? 'ready' : ''} /></div>
          <div className="runtime-row"><Laptop size={16} /><div><strong>Local Llama</strong><span>{runtime?.providers.llama.configured ? runtime.providers.llama.model : 'Runner offline'}</span></div><i className={runtime?.providers.llama.configured ? 'ready' : ''} /></div>
        </div>
      </aside>

      <section className="agent-workspace panel">
        <header className="agent-toolbar">
          <div className="agent-mode-control" aria-label="Agent mode">
            <button className={mode === 'research' ? 'active' : ''} disabled={!providerRuntime?.modes.includes('research')} onClick={() => setMode('research')}><Globe2 size={15} />Research</button>
            <button className={mode === 'trades' ? 'active' : ''} disabled={!providerRuntime?.modes.includes('trades')} onClick={() => setMode('trades')}><CheckCircle2 size={15} />Trade review</button>
            <button className={mode === 'portfolio' ? 'active' : ''} disabled={!providerRuntime?.modes.includes('portfolio')} onClick={() => setMode('portfolio')}><Database size={15} />Portfolio</button>
          </div>
          <div className="agent-provider-control" aria-label="Model provider">
            <button className={provider === 'gemini' ? 'active' : ''} onClick={() => selectProvider('gemini')}><Cloud size={15} />Gemini</button>
            <button className={provider === 'llama' ? 'active' : ''} onClick={() => selectProvider('llama')}><Laptop size={15} />Llama</button>
          </div>
        </header>

        <div className={`agent-stage ${activeRun ? 'has-result' : ''}`}>
          {error && <div className="page-alert error agent-error">{error}</div>}
          {activeRun ? (
            <article className="agent-result">
              <div className="agent-result-heading">
                <div><span>{activeRun.provider} / {activeRun.model}</span><h2>{activeRun.prompt}</h2></div>
                <strong className={`status-pill ${activeRun.status}`}>{activeRun.status}</strong>
              </div>
              {activeRun.answer && <div className="agent-answer">{activeRun.answer}</div>}
              {activeRun.error_message && <div className="page-alert error">{activeRun.error_message}</div>}
              {activeRun.sources.length > 0 && (
                <section className="agent-sources">
                  <h3>Sources</h3>
                  {activeRun.sources.map((source, index) => (
                    <a href={source.url} target="_blank" rel="noreferrer" key={`${source.url}-${index}`}>
                      <span>{index + 1}</span><div><strong>{source.title}</strong><small>{source.cited_text || source.url}</small></div>
                    </a>
                  ))}
                </section>
              )}
            </article>
          ) : (
            <>
              <div className="agent-stage-icon"><Bot size={24} /></div>
              <h2>What should we investigate?</h2>
              <div className="agent-suggestions">
                {suggestions[mode].map((suggestion) => (
                  <button key={suggestion} onClick={() => setPrompt(suggestion)}>{suggestion}</button>
                ))}
              </div>
            </>
          )}

          <form className="agent-composer" onSubmit={submit}>
            <Search size={18} />
            <textarea
              aria-label="Research task"
              placeholder={mode === 'research' ? 'Ask a public research question' : mode === 'trades' ? 'Ask about your closed-trade performance' : 'Ask about your portfolio performance'}
              rows={2}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
            />
            <button type="submit" className="agent-send" disabled={!canRun} title={!providerReady ? 'Selected provider is not configured' : !modeReady ? 'Selected mode is not connected yet' : 'Run agent'} aria-label="Run agent">
              <Send size={17} className={busy ? 'spin' : ''} />
            </button>
          </form>

          {mode === 'research' ? (
            <div className="agent-guardrails">
              <span><Globe2 size={14} />Source-backed web research</span>
              <span><ShieldCheck size={14} />Public prompts only</span>
              <span><BookOpenCheck size={14} />Citations required</span>
            </div>
          ) : (
            <div className="agent-guardrails">
              <span><Database size={14} />Verified TradeOS metrics</span>
              <span><Laptop size={14} />Local model</span>
              <span><ShieldCheck size={14} />Read-only analysis</span>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
