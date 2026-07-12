from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    broker_accounts: Mapped[list["BrokerAccount"]] = relationship(back_populates="user")


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    broker_name: Mapped[str] = mapped_column(String(80), default="Angel One")
    mode: Mapped[str] = mapped_column(String(20), default="demo")
    status: Mapped[str] = mapped_column(String(30), default="connected")
    client_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    feed_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_balance: Mapped[float] = mapped_column(Float, default=0)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    raw_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped[User] = relationship(back_populates="broker_accounts")


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    broker_account_id: Mapped[int] = mapped_column(ForeignKey("broker_accounts.id"))
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    records_synced: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (UniqueConstraint("user_id", "broker_trade_id", name="uq_user_broker_trade"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    broker_account_id: Mapped[int] = mapped_column(ForeignKey("broker_accounts.id"))
    broker_trade_id: Mapped[str] = mapped_column(String(120), index=True)
    symbol: Mapped[str] = mapped_column(String(40), index=True)
    exchange: Mapped[str] = mapped_column(String(20), default="NSE")
    segment: Mapped[str] = mapped_column(String(30), default="Equity")
    product: Mapped[str] = mapped_column(String(30), default="DELIVERY", index=True)
    direction: Mapped[str] = mapped_column(String(10), default="LONG")
    quantity: Mapped[int] = mapped_column(Integer)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_pnl: Mapped[float] = mapped_column(Float, default=0)
    charges: Mapped[float] = mapped_column(Float, default=0)
    net_pnl: Mapped[float] = mapped_column(Float, default=0, index=True)
    return_percent: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default="CLOSED", index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    entry_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    holding_minutes: Mapped[int] = mapped_column(Integer, default=0)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String(30), default="research")
    provider: Mapped[str] = mapped_column(String(30), default="gemini")
    model: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
    search_queries: Mapped[list | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
