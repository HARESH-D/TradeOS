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
import { FormEvent, useState } from 'react'

const suggestions = [
  'Research a company and build an evidence-backed briefing',
  'Review my imported trades for recurring behavioral patterns',
  'Compare portfolio performance across symbols and outcomes',
]

export function AgentPage() {
  const [mode, setMode] = useState<'research' | 'trades' | 'portfolio'>('research')
  const [provider, setProvider] = useState<'gemini' | 'llama'>('gemini')
  const [prompt, setPrompt] = useState('')

  function submit(event: FormEvent) {
    event.preventDefault()
  }

  return (
    <div className="agent-page">
      <aside className="agent-rail panel">
        <button className="primary-button agent-new-task" disabled title="Agent runtime is not configured">
          <Plus size={16} /> New task
        </button>

        <div className="agent-rail-section">
          <span className="agent-section-label">Research runs</span>
          <div className="agent-run-empty"><BookOpenCheck size={18} /><span>No runs yet</span></div>
        </div>

        <div className="agent-rail-section runtime-section">
          <span className="agent-section-label">Runtime</span>
          <div className="runtime-row"><Cloud size={16} /><div><strong>Gemini API</strong><span>Not configured</span></div><i /></div>
          <div className="runtime-row"><Laptop size={16} /><div><strong>Local Llama</strong><span>Runner offline</span></div><i /></div>
        </div>
      </aside>

      <section className="agent-workspace panel">
        <header className="agent-toolbar">
          <div className="agent-mode-control" aria-label="Agent mode">
            <button className={mode === 'research' ? 'active' : ''} onClick={() => setMode('research')}><Globe2 size={15} />Research</button>
            <button className={mode === 'trades' ? 'active' : ''} onClick={() => setMode('trades')}><CheckCircle2 size={15} />Trade review</button>
            <button className={mode === 'portfolio' ? 'active' : ''} onClick={() => setMode('portfolio')}><Database size={15} />Portfolio</button>
          </div>
          <div className="agent-provider-control" aria-label="Model provider">
            <button className={provider === 'gemini' ? 'active' : ''} onClick={() => setProvider('gemini')}><Cloud size={15} />Gemini</button>
            <button className={provider === 'llama' ? 'active' : ''} onClick={() => setProvider('llama')}><Laptop size={15} />Llama</button>
          </div>
        </header>

        <div className="agent-stage">
          <div className="agent-stage-icon"><Bot size={24} /></div>
          <h2>What should we investigate?</h2>
          <div className="agent-suggestions">
            {suggestions.map((suggestion) => (
              <button key={suggestion} onClick={() => setPrompt(suggestion)}>{suggestion}</button>
            ))}
          </div>

          <form className="agent-composer" onSubmit={submit}>
            <Search size={18} />
            <textarea
              aria-label="Research task"
              placeholder="Ask for research, trade analysis, or a portfolio review"
              rows={2}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
            />
            <button type="submit" className="agent-send" disabled title="Agent runtime is not configured" aria-label="Run agent">
              <Send size={17} />
            </button>
          </form>

          <div className="agent-guardrails">
            <span><Globe2 size={14} />Source-backed web research</span>
            <span><ShieldCheck size={14} />Read-only trading data</span>
            <span><BookOpenCheck size={14} />Citations required</span>
          </div>
        </div>
      </section>
    </div>
  )
}
