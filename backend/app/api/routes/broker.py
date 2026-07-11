from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.broker.angel_one import AngelOneAdapter, AngelOneError
from app.core.config import settings
from app.core.security import encrypt_secret
from app.db.models import BrokerAccount, SyncRun, User
from app.db.session import get_db
from app.schemas.api import BrokerConnectRequest
from app.services.sync_service import run_sync


router = APIRouter(prefix="/broker", tags=["broker"])


@router.get("/angel-one/callback", include_in_schema=False)
def angel_one_callback():
    return RedirectResponse(f"{settings.frontend_url.rstrip('/')}/broker?angel=callback-received", status_code=302)


def _account_response(account: BrokerAccount) -> dict:
    snapshot = account.raw_snapshot or {}
    return {
        "id": account.id,
        "broker_name": account.broker_name,
        "mode": account.mode,
        "status": account.status,
        "client_code": account.client_code,
        "account_balance": account.account_balance,
        "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
        "counts": {
            "holdings": len(snapshot.get("holdings", [])),
            "orders": len(snapshot.get("orders", [])),
            "positions": len(snapshot.get("positions", [])),
        },
    }


@router.get("")
def get_broker(user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = db.scalar(select(BrokerAccount).where(BrokerAccount.user_id == user.id).order_by(BrokerAccount.id.desc()))
    return _account_response(account) if account else {"status": "disconnected"}


@router.post("/connect")
async def connect_broker(payload: BrokerConnectRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = db.scalar(select(BrokerAccount).where(BrokerAccount.user_id == user.id).order_by(BrokerAccount.id.desc()))
    if not account:
        account = BrokerAccount(user_id=user.id)
        db.add(account)
    if payload.mode == "demo":
        account.mode = "demo"
        account.broker_name = "Angel One Demo"
        account.client_code = "DEMO01"
        account.status = "connected"
        account.api_key_encrypted = None
        account.access_token_encrypted = None
        db.commit()
        db.refresh(account)
        await run_sync(db, account)
        return _account_response(account)

    if not all([payload.api_key, payload.client_code, payload.pin, payload.totp]):
        raise HTTPException(status_code=422, detail="API key, client code, PIN and current TOTP are required")
    try:
        adapter = AngelOneAdapter(
            payload.api_key or "",
            public_ip=settings.broker_public_ip,
            local_ip=settings.broker_local_ip,
            mac_address=settings.broker_mac_address,
        )
        session = await adapter.connect(payload.client_code or "", payload.pin or "", payload.totp or "")
    except AngelOneError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    account.mode = "angel"
    account.broker_name = "Angel One"
    account.client_code = payload.client_code
    account.status = "connected"
    account.api_key_encrypted = encrypt_secret(payload.api_key)
    account.access_token_encrypted = encrypt_secret(session.access_token)
    account.refresh_token_encrypted = encrypt_secret(session.refresh_token)
    account.feed_token_encrypted = encrypt_secret(session.feed_token)
    db.commit()
    db.refresh(account)
    return _account_response(account)


@router.post("/sync")
async def sync_broker(user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = db.scalar(select(BrokerAccount).where(BrokerAccount.user_id == user.id).order_by(BrokerAccount.id.desc()))
    if not account:
        raise HTTPException(status_code=409, detail="Connect a broker before syncing")
    try:
        sync_run = await run_sync(db, account)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "id": sync_run.id,
        "status": sync_run.status,
        "completed_at": sync_run.completed_at.isoformat() if sync_run.completed_at else None,
        "records_synced": sync_run.records_synced,
        "details": sync_run.details,
    }


@router.get("/sync/history")
def sync_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    runs = db.scalars(select(SyncRun).where(SyncRun.user_id == user.id).order_by(SyncRun.started_at.desc()).limit(10)).all()
    return [
        {
            "id": run.id,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "records_synced": run.records_synced,
            "details": run.details,
            "error_message": run.error_message,
        }
        for run in runs
    ]
