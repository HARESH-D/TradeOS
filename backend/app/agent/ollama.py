import json

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.agent.contracts import AgentProviderError, AgentProviderUnavailable, ResearchResult
from app.core.config import settings


class AnalysisPattern(BaseModel):
    observation: str = Field(max_length=500)
    evidence: str = Field(max_length=500)
    confidence: str = Field(pattern="^(high|medium|low)$")


class StructuredAnalysis(BaseModel):
    summary: str = Field(max_length=1_000)
    patterns: list[AnalysisPattern] = Field(min_length=1, max_length=4)
    uncertainties: list[str] = Field(max_length=3)
    next_checks: list[str] = Field(min_length=3, max_length=3)


class OllamaAnalysisProvider:
    name = "llama"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        enabled: bool | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.enabled = settings.ollama_enabled if enabled is None else enabled
        self.client = client

    async def available(self) -> bool:
        if not self.enabled:
            return False
        try:
            if self.client:
                response = await self.client.get(f"{self.base_url}/api/tags")
            else:
                async with httpx.AsyncClient(timeout=settings.ollama_health_timeout_seconds) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            names = {str(item.get("name")) for item in response.json().get("models", [])}
            return self.model in names
        except (httpx.HTTPError, ValueError):
            return False

    async def analyze(self, prompt: str, mode: str, context: dict) -> ResearchResult:
        if not self.enabled:
            raise AgentProviderUnavailable("Local Llama is disabled")

        payload = {
            "model": self.model,
            "stream": False,
            "format": StructuredAnalysis.model_json_schema(),
            "options": {
                "temperature": 0,
                "num_ctx": settings.ollama_context_length,
                "num_predict": settings.ollama_max_output_tokens,
            },
            "messages": [
                {"role": "system", "content": self._system_instruction(mode)},
                {
                    "role": "user",
                    "content": (
                        f"User request:\n{prompt.strip()}\n\n"
                        "Verified TradeOS context (JSON):\n"
                        f"{json.dumps(context, separators=(',', ':'), ensure_ascii=True)}"
                    ),
                },
            ],
        }
        try:
            if self.client:
                response = await self.client.post(f"{self.base_url}/api/chat", json=payload)
            else:
                async with httpx.AsyncClient(timeout=settings.ollama_request_timeout_seconds) as client:
                    response = await client.post(f"{self.base_url}/api/chat", json=payload)
        except httpx.ConnectError as exc:
            raise AgentProviderUnavailable("The local Ollama runner is offline") from exc
        except httpx.HTTPError as exc:
            raise AgentProviderError("The local Ollama request failed") from exc

        if response.status_code == 404:
            raise AgentProviderUnavailable(f"Local model {self.model} is not installed")
        if response.status_code >= 400:
            raise AgentProviderError(f"Ollama request failed with status {response.status_code}")

        try:
            content = response.json()["message"]["content"]
            analysis = StructuredAnalysis.model_validate_json(content)
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise AgentProviderError("Ollama returned an invalid or incomplete analysis") from exc

        return ResearchResult(answer=self._render_answer(analysis, context))

    @staticmethod
    def _system_instruction(mode: str) -> str:
        focus = "closed-trade behavior" if mode == "trades" else "portfolio concentration and performance"
        return (
            f"You are the TradeOS read-only analyst for {focus}. All numeric context is calculated by deterministic "
            "application code and must be treated as authoritative. Interpret it without recalculating or inventing "
            "facts. Put the most material observation first, distinguish association from causation, state sample-size "
            "limits, and suggest checks that inspect existing records rather than changes to stops, sizing, strategy, or "
            "instruments. Never recommend securities to buy or sell. Keep every field concise."
        )

    @staticmethod
    def _render_answer(analysis: StructuredAnalysis, context: dict) -> str:
        metrics = context.get("headline_metrics", {})
        scope = context.get("scope", {})
        lines = [
            "SUMMARY",
            analysis.summary,
            "",
            "VERIFIED SNAPSHOT",
            f"- Closed trades: {metrics.get('trade_count', 0)}",
            f"- Net P&L: {metrics.get('net_pnl', 0):,.2f}",
            f"- Win rate: {metrics.get('win_rate', 0):.2f}%",
            f"- Profit factor: {metrics.get('profit_factor', 0):.2f}",
            f"- Expectancy per trade: {metrics.get('expectancy', 0):,.2f}",
            f"- Period: {scope.get('start_date') or 'n/a'} to {scope.get('end_date') or 'n/a'}",
            "",
            "OBSERVED PATTERNS",
        ]
        for pattern in analysis.patterns:
            lines.append(f"- {pattern.observation} ({pattern.confidence} confidence) Evidence: {pattern.evidence}")
        lines.extend(["", "UNCERTAINTIES"])
        lines.extend(f"- {item}" for item in analysis.uncertainties)
        lines.extend(["", "NEXT CHECKS"])
        lines.extend(f"{index}. {item}" for index, item in enumerate(analysis.next_checks, start=1))
        return "\n".join(lines)[:20_000]
