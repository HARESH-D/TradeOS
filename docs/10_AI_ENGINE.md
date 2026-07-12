# AI Engine

TradeOS AI is a source-backed research and retrospective analysis system. It explains trades, detects behavioral patterns, summarizes performance, and researches user questions. It never predicts prices or executes orders.

## Milestone 2

- Clean-room agent runtime based on publicly documented agent patterns
- Gemini API provider for cloud reasoning, grounded search, and citations
- Ollama provider for local tool-capable Llama models
- Typed, allowlisted tools for web research and read-only TradeOS analytics
- Persistent runs, evidence, sources, tool events, and checkpoints
- Human approval before any future side effect

## Implemented Research Slice

- Provider-neutral `ResearchProvider` contract
- Gemini Interactions API adapter using configurable `gemini-2.5-flash`
- Grounded Google Search query and citation extraction
- Persistent completed and failed `agent_runs`
- Authenticated provider status, create-run and history APIs
- Working research composer, run history, answers and source links

Research currently completes inline inside the API request. Durable queued execution, streaming, dedicated evidence rows, trade tools and local Llama remain subsequent slices.

The complete design and implementation sequence are documented in [27_AI_AGENT_MILESTONE.md](27_AI_AGENT_MILESTONE.md).
