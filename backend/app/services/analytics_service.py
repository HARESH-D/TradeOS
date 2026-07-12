from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BrokerAccount, Trade


def serialize_trade(trade: Trade) -> dict:
    return {
        "id": trade.id,
        "broker_trade_id": trade.broker_trade_id,
        "trade_date": trade.trade_date.isoformat(),
        "symbol": trade.symbol,
        "exchange": trade.exchange,
        "segment": trade.segment,
        "product": trade.product,
        "direction": trade.direction,
        "quantity": trade.quantity,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "gross_pnl": trade.gross_pnl,
        "charges": trade.charges,
        "net_pnl": trade.net_pnl,
        "return_percent": trade.return_percent,
        "status": trade.status,
        "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
        "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
        "holding_minutes": trade.holding_minutes,
    }


def dashboard_data(db: Session, user_id: int) -> dict:
    account = db.scalar(select(BrokerAccount).where(BrokerAccount.user_id == user_id).order_by(BrokerAccount.id.desc()))
    trade_filters = [Trade.user_id == user_id]
    if account:
        trade_filters.append(Trade.broker_account_id == account.id)
    trades = list(db.scalars(select(Trade).where(*trade_filters).order_by(Trade.trade_date)).all())
    closed = [trade for trade in trades if trade.status == "CLOSED"]
    winners = [trade for trade in closed if trade.net_pnl > 0]
    losers = [trade for trade in closed if trade.net_pnl < 0]
    net_pnl = sum(trade.net_pnl for trade in closed)
    gross_profit = sum(trade.net_pnl for trade in winners)
    gross_loss = abs(sum(trade.net_pnl for trade in losers))
    avg_win = gross_profit / len(winners) if winners else 0
    avg_loss = gross_loss / len(losers) if losers else 0
    win_rate = len(winners) / len(closed) * 100 if closed else 0
    expectancy = net_pnl / len(closed) if closed else 0
    profit_factor = gross_profit / gross_loss if gross_loss else 0

    daily: dict[date, dict] = defaultdict(lambda: {"pnl": 0.0, "trades": 0})
    for trade in closed:
        daily[trade.trade_date]["pnl"] += trade.net_pnl
        daily[trade.trade_date]["trades"] += 1

    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    series = []
    for day in sorted(daily):
        pnl = round(daily[day]["pnl"], 2)
        cumulative += pnl
        peak = max(peak, cumulative)
        drawdown = cumulative - peak
        max_drawdown = min(max_drawdown, drawdown)
        series.append({"date": day.isoformat(), "daily": pnl, "cumulative": round(cumulative, 2), "drawdown": round(drawdown, 2)})

    calendar = [
        {"date": day.isoformat(), "pnl": round(values["pnl"], 2), "trades": values["trades"]}
        for day, values in sorted(daily.items())
    ]
    recent = [serialize_trade(trade) for trade in sorted(trades, key=lambda item: item.trade_date, reverse=True)[:7]]
    snapshot = account.raw_snapshot if account and account.raw_snapshot else {}
    return {
        "broker": {
            "name": account.broker_name if account else None,
            "mode": account.mode if account else None,
            "status": account.status if account else "disconnected",
            "last_synced_at": account.last_synced_at.isoformat() if account and account.last_synced_at else None,
            "counts": {
                "holdings": len(snapshot.get("holdings", [])),
                "orders": len(snapshot.get("orders", [])),
                "positions": len(snapshot.get("positions", [])),
                "trades": len(trades),
            },
        },
        "metrics": {
            "account_balance": round(account.account_balance if account else 0, 2),
            "net_pnl": round(net_pnl, 2),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "max_drawdown": round(max_drawdown, 2),
            "trade_count": len(closed),
            "winner_count": len(winners),
            "loser_count": len(losers),
        },
        "series": series,
        "calendar": calendar,
        "recent_trades": recent,
    }
