import asyncio
import json
from datetime import date

import httpx
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.agent.contracts import AgentProviderUnavailable, ResearchResult, ResearchSource
from app.agent.gemini import GeminiResearchProvider
from app.agent.ollama import OllamaAnalysisProvider
from app.db.models import AgentRun, Base, BrokerAccount, Trade, User
from app.services.agent_service import list_agent_runs, run_analysis, run_research
from app.services.analytics_service import agent_analysis_context


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


class FakeAnalysisProvider:
    name = "llama"
    model = "test-llama"

    async def analyze(self, prompt: str, mode: str, context: dict) -> ResearchResult:
        return ResearchResult(answer=f"{mode}: {prompt}; trades={context['headline_metrics']['trade_count']}")


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


def test_ollama_provider_discovers_model_and_parses_structured_analysis():
    structured = {
        "summary": "Loss size outweighed a positive win rate.",
        "patterns": [
            {
                "observation": "Losses were larger than wins.",
                "evidence": "Average loss exceeded average win.",
                "confidence": "high",
            }
        ],
        "uncertainties": ["The sample is small."],
        "next_checks": ["Review loss exits.", "Segment by symbol.", "Compare holding times."],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama-test"}]})
        payload = json.loads(request.content)
        assert payload["model"] == "llama-test"
        assert payload["stream"] is False
        assert payload["format"]["type"] == "object"
        return httpx.Response(200, json={"message": {"content": json.dumps(structured)}})

    async def call_provider():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            provider = OllamaAnalysisProvider(
                base_url="http://127.0.0.1:11434", model="llama-test", enabled=True, client=client
            )
            assert await provider.available() is True
            return await provider.analyze(
                "Review my trades",
                "trades",
                {
                    "scope": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
                    "headline_metrics": {
                        "trade_count": 8,
                        "net_pnl": -1500,
                        "win_rate": 62.5,
                        "profit_factor": 0.81,
                        "expectancy": -187.5,
                    },
                },
            )

    result = asyncio.run(call_provider())

    assert "Closed trades: 8" in result.answer
    assert "Losses were larger than wins" in result.answer
    assert "Review loss exits" in result.answer


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


def test_trade_analysis_context_is_deterministic_and_user_scoped():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = create_user(db)
        other_user = create_user(db, "context-other@tradeos.app")
        account = BrokerAccount(
            user_id=user.id,
            broker_name="Test",
            mode="demo",
            account_balance=50_000,
            raw_snapshot={
                "holdings": [{"symbol": "NIFTY", "quantity": 1, "api_key": "must-not-reach-model"}],
                "positions": [],
            },
        )
        other_account = BrokerAccount(user_id=other_user.id, broker_name="Test", mode="demo")
        db.add_all([account, other_account])
        db.flush()
        db.add_all(
            [
                Trade(
                    user_id=user.id,
                    broker_account_id=account.id,
                    broker_trade_id="winner",
                    symbol="NIFTY",
                    direction="LONG",
                    quantity=1,
                    entry_price=100,
                    exit_price=110,
                    net_pnl=1_000,
                    status="CLOSED",
                    trade_date=date(2026, 1, 2),
                    holding_minutes=60,
                ),
                Trade(
                    user_id=user.id,
                    broker_account_id=account.id,
                    broker_trade_id="loser",
                    symbol="BANKNIFTY",
                    direction="SHORT",
                    quantity=1,
                    entry_price=100,
                    exit_price=80,
                    net_pnl=-2_000,
                    status="CLOSED",
                    trade_date=date(2026, 1, 3),
                    holding_minutes=10,
                ),
                Trade(
                    user_id=other_user.id,
                    broker_account_id=other_account.id,
                    broker_trade_id="other",
                    symbol="SECRET",
                    direction="LONG",
                    quantity=1,
                    entry_price=1,
                    exit_price=2,
                    net_pnl=99_999,
                    status="CLOSED",
                    trade_date=date(2026, 1, 4),
                ),
            ]
        )
        db.commit()

        context = agent_analysis_context(db, user.id, "trades")
        run = asyncio.run(
            run_analysis(db, user.id, "Find my largest process risk", "trades", context, FakeAnalysisProvider())
        )

        assert context["headline_metrics"]["trade_count"] == 2
        assert context["headline_metrics"]["net_pnl"] == -1_000
        assert context["outcome_metrics"]["average_winner_hold_minutes"] == 60
        assert context["outcome_metrics"]["average_loser_hold_minutes"] == 10
        assert {row["name"] for row in context["by_symbol"]} == {"NIFTY", "BANKNIFTY"}
        assert run.mode == "trades"
        assert run.provider == "llama"

        portfolio_context = agent_analysis_context(db, user.id, "portfolio")
        assert portfolio_context["portfolio"]["holdings"] == [{"symbol": "NIFTY", "quantity": 1}]
