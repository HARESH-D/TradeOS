import asyncio

import httpx
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.agent.contracts import AgentProviderUnavailable, ResearchResult, ResearchSource
from app.agent.gemini import GeminiResearchProvider
from app.db.models import AgentRun, Base, User
from app.services.agent_service import list_agent_runs, run_research


class FakeResearchProvider:
    name = "fake"
    model = "fake-research-v1"

    async def research(self, prompt: str) -> ResearchResult:
        return ResearchResult(
            answer=f"Evidence-backed answer for: {prompt}",
            sources=[ResearchSource(url="https://example.com/report", title="Example report", cited_text="answer")],
            search_queries=["example research query"],
        )


class UnavailableProvider:
    name = "fake"
    model = "offline"

    async def research(self, prompt: str) -> ResearchResult:
        raise AgentProviderUnavailable("Provider is offline")


def create_user(db: Session, email: str = "agent@tradeos.app") -> User:
    user = User(email=email, name="Agent Test", password_hash="unused")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_gemini_provider_parses_answer_queries_and_unique_citations():
    response_payload = {
        "steps": [
            {"type": "google_search_call", "arguments": {"queries": ["primary query", "primary query"]}},
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": "A supported claim.",
                        "annotations": [
                            {
                                "type": "url_citation",
                                "url": "https://example.com/source",
                                "title": "Primary source",
                                "start_index": 0,
                                "end_index": 17,
                            },
                            {
                                "type": "url_citation",
                                "url": "javascript:alert(1)",
                                "title": "Unsafe source",
                                "start_index": 0,
                                "end_index": 17,
                            },
                            {
                                "type": "url_citation",
                                "url": "https://example.com/source",
                                "title": "Primary source",
                                "start_index": 0,
                                "end_index": 17,
                            },
                        ],
                    }
                ],
            },
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "test-key"
        return httpx.Response(200, json=response_payload)

    async def call_provider():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            provider = GeminiResearchProvider(api_key="test-key", model="test-model", client=client)
            return await provider.research("Research this")

    result = asyncio.run(call_provider())

    assert result.answer == "A supported claim."
    assert result.search_queries == ["primary query"]
    assert len(result.sources) == 1
    assert result.sources[0].title == "Primary source"
    assert result.sources[0].cited_text == "A supported claim"


def test_agent_run_persists_result_and_is_scoped_to_user():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = create_user(db)
        other_user = create_user(db, "other@tradeos.app")

        run = asyncio.run(run_research(db, user.id, "Research the market structure", FakeResearchProvider()))

        assert run.status == "completed"
        assert run.provider == "fake"
        assert run.sources[0]["url"] == "https://example.com/report"
        assert len(list_agent_runs(db, user.id)) == 1
        assert list_agent_runs(db, other_user.id) == []


def test_agent_run_records_provider_failure():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = create_user(db)

        with pytest.raises(AgentProviderUnavailable, match="offline"):
            asyncio.run(run_research(db, user.id, "Research a valid question", UnavailableProvider()))

        assert db.scalar(select(func.count(AgentRun.id))) == 1
        run = db.scalar(select(AgentRun))
        assert run is not None
        assert run.status == "failed"
        assert run.completed_at is not None
        assert run.error_message == "Provider is offline"
