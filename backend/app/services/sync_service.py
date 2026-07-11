from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.broker.angel_one import AngelOneAdapter
from app.broker.base import BrokerSnapshot
from app.broker.mock import MockBrokerAdapter
from app.core.config import settings
from app.core.security import decrypt_secret
from app.db.models import BrokerAccount, SyncRun, Trade


def _number(value, default=0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for parser in (
        lambda raw: date.fromisoformat(raw[:10]),
        lambda raw: datetime.strptime(raw, "%d-%b-%Y %H:%M:%S").date(),
        lambda raw: datetime.strptime(raw, "%d-%b-%Y").date(),
        lambda raw: datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").date(),
    ):
        try:
            return parser(text)
        except ValueError:
            continue
    return datetime.now(UTC).date()


def _parse_datetime(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    for pattern in ("%d-%b-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def _normalize_trade(row: dict, mode: str, index: int) -> dict:
    if mode == "demo":
        return row
    price = _number(row.get("fillprice") or row.get("price") or row.get("averageprice"))
    quantity = int(_number(row.get("fillsize") or row.get("quantity")))
    trade_id = str(row.get("tradeid") or row.get("orderid") or f"ANGEL-{index}")
    side = str(row.get("transactiontype") or "BUY").upper()
    trade_date = _parse_date(row.get("filltime") or row.get("updatetime") or row.get("exchtime"))
    return {
        "broker_trade_id": trade_id,
        "symbol": str(row.get("tradingsymbol") or row.get("symbol") or "UNKNOWN"),
        "exchange": str(row.get("exchange") or "NSE"),
        "segment": str(row.get("exchange") or "Equity"),
        "product": str(row.get("producttype") or "DELIVERY"),
        "direction": "LONG" if side == "BUY" else "SELL",
        "quantity": quantity,
        "entry_price": price,
        "exit_price": None,
        "gross_pnl": 0,
        "charges": 0,
        "net_pnl": 0,
        "return_percent": 0,
        "status": "EXECUTED",
        "trade_date": trade_date.isoformat(),
        "entry_time": row.get("filltime") or row.get("updatetime"),
        "exit_time": None,
        "holding_minutes": 0,
        "raw_data": row,
    }


async def run_sync(db: Session, account: BrokerAccount) -> SyncRun:
    sync_run = SyncRun(user_id=account.user_id, broker_account_id=account.id, status="running")
    db.add(sync_run)
    db.commit()
    db.refresh(sync_run)
    try:
        if account.mode == "demo":
            adapter = MockBrokerAdapter()
        else:
            adapter = AngelOneAdapter(
                api_key=decrypt_secret(account.api_key_encrypted) or "",
                access_token=decrypt_secret(account.access_token_encrypted),
                refresh_token=decrypt_secret(account.refresh_token_encrypted),
                public_ip=settings.broker_public_ip,
                local_ip=settings.broker_local_ip,
                mac_address=settings.broker_mac_address,
            )
        snapshot = await adapter.fetch_snapshot()
        records = _persist_snapshot(db, account, snapshot)
        completed_at = datetime.now(UTC).replace(tzinfo=None)
        account.last_synced_at = completed_at
        account.status = "connected"
        sync_run.status = "completed"
        sync_run.completed_at = completed_at
        sync_run.records_synced = records
        sync_run.details = {
            "holdings": len(snapshot.holdings),
            "orders": len(snapshot.orders),
            "trades": len(snapshot.trades),
            "positions": len(snapshot.positions),
        }
        db.commit()
        db.refresh(sync_run)
        return sync_run
    except Exception as exc:
        account.status = "attention"
        sync_run.status = "failed"
        sync_run.completed_at = datetime.now(UTC).replace(tzinfo=None)
        sync_run.error_message = str(exc)
        db.commit()
        raise


def _persist_snapshot(db: Session, account: BrokerAccount, snapshot: BrokerSnapshot) -> int:
    rms = snapshot.rms
    account.account_balance = _number(rms.get("net") or rms.get("availablecash") or rms.get("netvalue"))
    account.raw_snapshot = {
        "profile": snapshot.profile,
        "holdings": snapshot.holdings,
        "orders": snapshot.orders,
        "positions": snapshot.positions,
        "rms": snapshot.rms,
    }
    for index, source in enumerate(snapshot.trades):
        row = _normalize_trade(source, account.mode, index)
        existing = db.scalar(
            select(Trade).where(
                Trade.user_id == account.user_id,
                Trade.broker_trade_id == str(row["broker_trade_id"]),
            )
        )
        trade = existing or Trade(
            user_id=account.user_id,
            broker_account_id=account.id,
            broker_trade_id=str(row["broker_trade_id"]),
            symbol=str(row["symbol"]),
            quantity=int(row["quantity"]),
            entry_price=float(row["entry_price"]),
            trade_date=_parse_date(row["trade_date"]),
        )
        trade.broker_account_id = account.id
        trade.symbol = str(row["symbol"])
        trade.exchange = str(row.get("exchange") or "NSE")
        trade.segment = str(row.get("segment") or "Equity")
        trade.product = str(row.get("product") or "DELIVERY")
        trade.direction = str(row.get("direction") or "LONG")
        trade.quantity = int(row.get("quantity") or 0)
        trade.entry_price = _number(row.get("entry_price"))
        trade.exit_price = _number(row.get("exit_price")) if row.get("exit_price") is not None else None
        trade.gross_pnl = _number(row.get("gross_pnl"))
        trade.charges = _number(row.get("charges"))
        trade.net_pnl = _number(row.get("net_pnl"))
        trade.return_percent = _number(row.get("return_percent"))
        trade.status = str(row.get("status") or "CLOSED")
        trade.trade_date = _parse_date(row.get("trade_date"))
        trade.entry_time = _parse_datetime(row.get("entry_time"))
        trade.exit_time = _parse_datetime(row.get("exit_time"))
        trade.holding_minutes = int(row.get("holding_minutes") or 0)
        trade.raw_data = row.get("raw_data") or source
        db.add(trade)
    db.commit()
    return len(snapshot.holdings) + len(snapshot.orders) + len(snapshot.trades) + len(snapshot.positions) + 1
