from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.contracts import ResearchProvider
from app.agent.gemini import GeminiResearchProvider
from app.db.models import AgentRun


def agent_run_response(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "mode": run.mode,
        "provider": run.provider,
        "model": run.model,
        "status": run.status,
        "prompt": run.prompt,
        "answer": run.answer,
        "sources": run.sources or [],
        "search_queries": run.search_queries or [],
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def list_agent_runs(db: Session, user_id: int, limit: int = 20) -> list[AgentRun]:
    return list(
        db.scalars(
            select(AgentRun).where(AgentRun.user_id == user_id).order_by(AgentRun.created_at.desc()).limit(limit)
        ).all()
    )


async def run_research(
    db: Session,
    user_id: int,
    prompt: str,
    provider: ResearchProvider | None = None,
) -> AgentRun:
    selected = provider or GeminiResearchProvider()
    run = AgentRun(
        user_id=user_id,
        mode="research",
        provider=selected.name,
        model=selected.model,
        status="running",
        prompt=prompt.strip(),
        sources=[],
        search_queries=[],
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        result = await selected.research(run.prompt)
        run.answer = result.answer
        run.sources = [source.__dict__ for source in result.sources]
        run.search_queries = result.search_queries
        run.status = "completed"
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.completed_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        raise

    run.completed_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(run)
    return run
