from dataclasses import dataclass, field
from typing import Protocol


class AgentProviderError(RuntimeError):
    pass


class AgentProviderUnavailable(AgentProviderError):
    pass


@dataclass
class ResearchSource:
    url: str
    title: str
    cited_text: str = ""


@dataclass
class ResearchResult:
    answer: str
    sources: list[ResearchSource] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)


class ResearchProvider(Protocol):
    name: str
    model: str

    async def research(self, prompt: str) -> ResearchResult: ...


class AnalysisProvider(Protocol):
    name: str
    model: str

    async def analyze(self, prompt: str, mode: str, context: dict) -> ResearchResult: ...
