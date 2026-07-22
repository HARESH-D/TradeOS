from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agent.contracts import AgentProviderError, AgentProviderUnavailable
from app.agent.ollama import OllamaAnalysisProvider
from app.api.deps import current_user
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.api import AgentRunRequest
from app.services.agent_service import agent_run_response, list_agent_runs, run_analysis, run_research
from app.services.analytics_service import agent_analysis_context

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/status")
async def agent_status(user: User = Depends(current_user)):
    llama = OllamaAnalysisProvider()
    llama_available = await llama.available()
    return {
        "providers": {
            "gemini": {
                "configured": bool(settings.gemini_api_key),
                "model": settings.gemini_model,
                "modes": ["research"],
            },
            "llama": {
                "configured": llama_available,
                "model": settings.ollama_model,
                "modes": ["trades", "portfolio"],
            },
        },
        "modes": {"research": True, "trades": True, "portfolio": True},
    }


@router.get("/runs")
def get_agent_runs(
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return [agent_run_response(run) for run in list_agent_runs(db, user.id, limit)]


@router.post("/runs")
async def create_agent_run(
    payload: AgentRunRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    try:
        if payload.provider == "gemini":
            if payload.mode != "research":
                raise HTTPException(status_code=409, detail="Gemini is currently limited to public web research")
            run = await run_research(db, user.id, payload.prompt)
        else:
            if payload.mode == "research":
                raise HTTPException(status_code=409, detail="Local web research is not connected yet")
            provider = OllamaAnalysisProvider()
            context = agent_analysis_context(db, user.id, payload.mode)
            run = await run_analysis(db, user.id, payload.prompt, payload.mode, context, provider)
    except AgentProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AgentProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return agent_run_response(run)
