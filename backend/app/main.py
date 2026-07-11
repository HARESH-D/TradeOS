from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select

from app.api.routes import analytics, auth, broker
from app.core.config import settings
from app.core.security import hash_password
from app.db.models import BrokerAccount, User
from app.db.session import Base, SessionLocal, engine
from app.services.sync_service import run_sync


async def seed_demo() -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "demo@tradeos.app"))
        if not user:
            user = User(email="demo@tradeos.app", name="Haresh", password_hash=hash_password("tradeos123"))
            db.add(user)
            db.commit()
            db.refresh(user)
        account = db.scalar(select(BrokerAccount).where(BrokerAccount.user_id == user.id))
        if not account:
            account = BrokerAccount(
                user_id=user.id,
                broker_name="Angel One Demo",
                mode="demo",
                status="connected",
                client_code="DEMO01",
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        if not account.last_synced_at:
            await run_sync(db, account)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo:
        await seed_demo()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(broker.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}
