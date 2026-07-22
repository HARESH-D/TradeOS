# Milestone 2: TradeOS AI Agent

## 1. Decision

TradeOS will not copy leaked, decompiled, or unlicensed Claude Code internals. The agent is a clean-room implementation based on public documentation, public APIs, and open-source runtimes with compatible licenses.

The useful public pattern is straightforward: gather context, act through tools, verify the result, and repeat until the task is complete or human input is required. Specialized workers receive isolated context and return concise findings to a coordinating agent.

## 2. Product Scope

The first agent will:

1. Research a user question using current web sources.
2. Build an evidence ledger containing claims, excerpts, timestamps, and source URLs.
3. Analyze evidence alongside read-only TradeOS metrics.
4. Produce a structured answer with claim-level citations and uncertainty.
5. Save the run so it can be resumed, audited, and evaluated.

It will not predict prices, place orders, modify broker data, execute arbitrary shell commands, or treat web-page instructions as trusted commands.

## 3. Architecture

```text
React Agent Workspace
        |
FastAPI Agent API
        |
Run Coordinator / State Machine
        |
        +-- Model Router
        |     +-- Gemini provider
        |     +-- Ollama/Llama provider through local runner
        |
        +-- Tool Registry
        |     +-- web_search
        |     +-- fetch_web_page
        |     +-- read_trade_metrics
        |     +-- query_trade_rows
        |     +-- calculate_statistics
        |
        +-- Research Workers
        |     +-- source discovery
        |     +-- extraction
        |     +-- trading analysis
        |     +-- claim verification
        |
        +-- PostgreSQL
              +-- agent_runs
              +-- agent_messages
              +-- tool_events
              +-- evidence_items
              +-- checkpoints
```

## 4. Agent Loop

1. **Classify:** determine whether the task is web research, trade review, portfolio analysis, or a combination.
2. **Plan:** produce bounded subtasks, source requirements, and a tool budget.
3. **Gather:** run independent searches in parallel when the questions do not depend on each other.
4. **Extract:** convert sources into typed evidence records; web content is data, never instructions.
5. **Analyze:** use deterministic code for financial calculations and the LLM for interpretation.
6. **Verify:** check every material claim against evidence, flag conflicts, and remove unsupported claims.
7. **Synthesize:** return the answer with citations, dates, limitations, and confidence.
8. **Checkpoint:** persist state after every stage so failed or rate-limited runs can resume.

Start as a deterministic workflow with one coordinating model. Add orchestrator-worker delegation only for broad research that benefits from parallel source discovery. A large permanent multi-agent hierarchy would increase cost, latency, and failure modes without improving simple tasks.

## 5. Provider Strategy

### Gemini

Gemini is the first cloud provider because its API supports function calling and grounded Google Search with returned citations. The model name must be configuration, not application logic, so free-tier model availability can change without a code deployment.

The first implementation defaults to `gemini-2.5-flash` because its current free tier includes a limited grounded-search allowance. Newer models may expose different billing rules. Recheck official pricing before changing the production model.

Store `GEMINI_API_KEY` only in backend environment variables. Enforce per-user and global budgets, retry `429` responses with jitter, and expose quota exhaustion as a resumable run state.

Free-tier provider terms may permit submitted content to be used for service improvement. Until explicit consent and provider-data controls exist, Gemini research accepts public research prompts only and does not receive imported portfolio or broker data.

### Local Llama

Ollama exposes tool calling and multi-turn agent loops for supported local models. The provider interface should match Gemini at the TradeOS boundary even when provider payloads differ.

The Vercel backend cannot call `localhost` on the user's computer. Local inference therefore requires a TradeOS local runner that makes an authenticated outbound connection, claims queued model jobs, sends results back, and never accepts public inbound traffic. Runs remain queued or can fall back to Gemini while the runner is offline.

The development adapter is now implemented for trade review and portfolio analysis when FastAPI and Ollama run on the same machine. It discovers the configured model through `/api/tags`, sends only user-scoped deterministic aggregates and allowlisted portfolio fields, validates a bounded JSON schema, and renders the answer server-side. Hosted companion transport remains pending.

### Local Model Evaluation

On the current Ryzen 5 4600H, 22 GiB RAM and GTX 1650 Ti 4 GiB development machine:

| Model | Quantized size | Observed speed | Decision |
|---|---:|---:|---|
| Llama 3.1 8B Q4_K_M | 4.9 GB | about 8 tokens/s | Selected minimum quality tier |
| Llama 3.2 3B | 2.0 GB | about 57 tokens/s | Rejected after row and outcome hallucinations |

The 8B model also made arithmetic errors when given raw rows. With a deterministic metrics tool it produced the correct tool call and preserved supplied metrics. Therefore TradeOS never delegates calculations to the model: application code computes facts, while Llama performs bounded interpretation. These measurements are machine-specific and must be rerun when hardware, runtime, quantization or prompts change.

## 6. Core Contracts

```text
ModelProvider.complete(messages, tools, limits) -> ModelTurn
Tool.execute(validated_arguments, user_context) -> ToolResult
RunStore.load(run_id, user_id) -> AgentRun
RunStore.checkpoint(run_id, state, events) -> Checkpoint
Policy.authorize(tool_call, user_context) -> allow | approval | deny
```

All tool arguments and results use versioned JSON schemas. Provider-specific SDK objects must not cross the provider adapter boundary.

## 7. Security Rules

- Scope every run, message, event, and evidence record to the authenticated user.
- Encrypt provider keys and never return them to the browser.
- Reject private, loopback, link-local, and metadata-service addresses in web-fetch tools.
- Allow only HTTP and HTTPS, enforce redirects, response-size limits, timeouts, and content-type checks.
- Remove scripts and active content before extraction.
- Mark retrieved text as untrusted and ignore instructions embedded in sources.
- Keep trading tools read-only; never provide broker tokens to the model.
- Require approval for future writes, communications, exports, or financial side effects.
- Log tool name, arguments hash, timing, result status, model, prompt version, and token usage without secrets.

## 8. Quality Bar

Measure the system with a fixed evaluation set:

- Citation precision: cited source directly supports the claim.
- Citation coverage: material claims have citations.
- Numerical correctness: calculated metrics match deterministic fixtures.
- Freshness: time-sensitive answers use current sources.
- Source quality: primary sources are preferred and conflicts are disclosed.
- Tool success and recovery rate.
- Cost, latency, and token use per completed task.
- Prompt-injection resistance and user-data isolation.

The verifier is not allowed to approve its own unsupported claim merely because another model generated similar wording. Verification operates on source evidence and deterministic results.

## 9. Delivery Slices

### Slice A: Workspace

- [x] AI Agent navigation and route
- [x] Research, trade review, and portfolio mode surfaces
- [x] Provider status and run history
- [x] Composer gated by actual runtime capability

### Slice B: Grounded Research

- [x] Gemini provider adapter
- [x] Grounded Search and citation rendering
- [x] Persistent completed and failed runs
- [ ] Dedicated URL fetch and normalized evidence extraction
- [ ] Server-sent event streaming
- [ ] Rate limits and run budgets

### Slice C: Trade Analyst

- [x] Read-only dashboard and analysis context
- [x] Deterministic calculations
- [x] Initial retrospective trade review and pattern reports

### Slice D: Local Models

- [x] Ollama provider adapter for same-machine development
- [x] Capability and installed-model discovery
- [ ] Authenticated local companion runner
- [ ] Cloud fallback policy

### Slice E: Reliability

- Durable workflow/checkpoints
- Human approval interrupts
- Evaluation suite, observability, and prompt-injection tests

## 10. Public References

- [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Gemini grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
