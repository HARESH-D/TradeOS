from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

from app.agent.contracts import (
    AgentProviderError,
    AgentProviderUnavailable,
    ResearchResult,
    ResearchSource,
)
from app.core.config import settings


class GeminiResearchProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        api_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.api_url = api_url or settings.gemini_api_url
        self.client = client

    async def research(self, prompt: str) -> ResearchResult:
        if not self.api_key:
            raise AgentProviderUnavailable("Gemini is not configured")

        payload = {
            "model": self.model,
            "input": prompt,
            "system_instruction": self._system_instruction(),
            "tools": [{"type": "google_search"}],
            "store": False,
        }
        try:
            if self.client:
                response = await self.client.post(
                    self.api_url,
                    headers={"x-goog-api-key": self.api_key},
                    json=payload,
                )
            else:
                async with httpx.AsyncClient(timeout=settings.agent_request_timeout_seconds) as client:
                    response = await client.post(
                        self.api_url,
                        headers={"x-goog-api-key": self.api_key},
                        json=payload,
                    )
        except httpx.HTTPError as exc:
            raise AgentProviderError("Gemini could not be reached") from exc

        if response.status_code == 429:
            raise AgentProviderError("Gemini free-tier quota is temporarily exhausted")
        if response.status_code >= 400:
            raise AgentProviderError(f"Gemini request failed with status {response.status_code}")
        return self._parse_response(response.json())

    def _system_instruction(self) -> str:
        today = datetime.now(UTC).date().isoformat()
        return (
            "You are the TradeOS research agent. Research the user's question using current, credible web sources. "
            "Prefer primary sources, distinguish facts from inference, disclose conflicts and uncertainty, and do not "
            "invent citations. Do not predict security prices or present the response as individualized financial advice. "
            f"The current date is {today}. Return a concise but substantive evidence-backed analysis."
        )

    @staticmethod
    def _parse_response(payload: dict) -> ResearchResult:
        answer_parts: list[str] = []
        queries: list[str] = []
        sources_by_url: dict[str, ResearchSource] = {}

        for step in payload.get("steps", []):
            if step.get("type") == "google_search_call":
                queries.extend(str(query) for query in step.get("arguments", {}).get("queries", []))
            if step.get("type") != "model_output":
                continue
            for block in step.get("content", []):
                if block.get("type") != "text" or not block.get("text"):
                    continue
                text = str(block["text"])
                answer_parts.append(text)
                for annotation in block.get("annotations", []):
                    if annotation.get("type") != "url_citation" or not annotation.get("url"):
                        continue
                    url = str(annotation["url"])
                    parsed_url = urlparse(url)
                    if parsed_url.scheme != "https" or not parsed_url.hostname:
                        continue
                    start = max(0, int(annotation.get("start_index", 0)))
                    end = max(start, int(annotation.get("end_index", start)))
                    sources_by_url.setdefault(
                        url,
                        ResearchSource(
                            url=url,
                            title=str(annotation.get("title") or parsed_url.hostname)[:300],
                            cited_text=text[start:end][:1_000],
                        ),
                    )

        answer = "\n\n".join(answer_parts).strip()[:20_000]
        if not answer:
            raise AgentProviderError("Gemini returned no research answer")
        return ResearchResult(answer=answer, sources=list(sources_by_url.values()), search_queries=list(dict.fromkeys(queries)))
