from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agent.contracts import AgentProviderError, AgentProviderUnavailable
from app.api.deps import current_user
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.api import AgentRunRequest
from app.services.agent_service import agent_run_response, list_agent_runs, run_research

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/status")
def agent_status(user: User = Depends(current_user)):
    return {
        "providers": {
            "gemini": {"configured": bool(settings.gemini_api_key), "model": settings.gemini_model},
            "llama": {"configured": False, "model": None},
        },
        "modes": {"research": True, "trades": False, "portfolio": False},
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
    if payload.mode != "research":
        raise HTTPException(status_code=409, detail="This analysis mode is planned but not connected yet")
    if payload.provider != "gemini":
        raise HTTPException(status_code=409, detail="The local Llama runner is not connected yet")
    try:
        run = await run_research(db, user.id, payload.prompt)
    except AgentProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AgentProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return agent_run_response(run)
