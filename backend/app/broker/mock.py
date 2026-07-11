import random
from datetime import UTC, datetime, timedelta

from app.broker.base import BrokerAdapter, BrokerSession, BrokerSnapshot


class MockBrokerAdapter(BrokerAdapter):
    async def connect(self, client_code: str = "DEMO01", pin: str = "", totp: str = "") -> BrokerSession:
        return BrokerSession(access_token="demo-token", profile={"clientcode": client_code, "name": "Demo Trader"})

    async def fetch_snapshot(self) -> BrokerSnapshot:
        rng = random.Random(41)
        today = datetime.now(UTC).date()
        symbols = ["RELIANCE", "HDFCBANK", "TCS", "INFY", "ICICIBANK", "SBIN", "TATAMOTORS", "LT"]
        products = ["DELIVERY", "DELIVERY", "DELIVERY", "SWING"]
        trades: list[dict] = []

        for index in range(42):
            days_ago = 2 + index * 2
            trade_day = today - timedelta(days=days_ago)
            symbol = symbols[index % len(symbols)]
            quantity = rng.choice([5, 8, 10, 12, 15, 20, 25])
            entry = round(rng.uniform(420, 3_250), 2)
            if index % 5 in (0, 1, 2):
                move = rng.uniform(0.012, 0.058)
            else:
                move = -rng.uniform(0.008, 0.042)
            exit_price = round(entry * (1 + move), 2)
            gross = round((exit_price - entry) * quantity, 2)
            turnover = (entry + exit_price) * quantity
            charges = round(max(12.5, turnover * 0.00072), 2)
            net = round(gross - charges, 2)
            entry_time = datetime.combine(trade_day - timedelta(days=rng.choice([1, 2, 3, 5, 8])), datetime.min.time()).replace(hour=10, minute=15)
            exit_time = datetime.combine(trade_day, datetime.min.time()).replace(hour=14, minute=35)
            trades.append(
                {
                    "broker_trade_id": f"DEMO-{trade_day:%Y%m%d}-{index:03d}",
                    "symbol": symbol,
                    "exchange": "NSE",
                    "segment": "Equity",
                    "product": products[index % len(products)],
                    "direction": "LONG",
                    "quantity": quantity,
                    "entry_price": entry,
                    "exit_price": exit_price,
                    "gross_pnl": gross,
                    "charges": charges,
                    "net_pnl": net,
                    "return_percent": round(move * 100, 2),
                    "status": "CLOSED",
                    "trade_date": trade_day.isoformat(),
                    "entry_time": entry_time.isoformat(),
                    "exit_time": exit_time.isoformat(),
                    "holding_minutes": int((exit_time - entry_time).total_seconds() // 60),
                }
            )

        holdings = [
            {"symbol": "RELIANCE", "quantity": 12, "average_price": 2860.2, "ltp": 2934.4},
            {"symbol": "HDFCBANK", "quantity": 20, "average_price": 1684.5, "ltp": 1721.15},
            {"symbol": "TCS", "quantity": 8, "average_price": 3921.0, "ltp": 4015.8},
        ]
        positions = [{"symbol": "INFY", "quantity": 10, "pnl": 842.5, "product": "DELIVERY"}]
        return BrokerSnapshot(
            profile={"clientcode": "DEMO01", "name": "Demo Trader", "email": "demo@tradeos.app"},
            holdings=holdings,
            orders=[],
            trades=trades,
            positions=positions,
            rms={"availablecash": 284650.75, "utiliseddebits": 74210.4, "net": 358861.15},
        )
