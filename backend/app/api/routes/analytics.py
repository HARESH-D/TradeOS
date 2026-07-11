from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.models import Trade, User
from app.db.session import get_db
from app.services.analytics_service import dashboard_data, serialize_trade


router = APIRouter(tags=["analytics"])


@router.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return dashboard_data(db, user.id)


@router.get("/analysis")
def analysis_grid(
    search: str | None = None,
    product: str | None = None,
    outcome: str | None = Query(default=None, pattern="^(win|loss|flat)$"),
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: str = "trade_date",
    sort_direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=250, ge=1, le=500),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    filters = [Trade.user_id == user.id]
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Trade.symbol.ilike(term), Trade.broker_trade_id.ilike(term)))
    if product and product != "ALL":
        filters.append(Trade.product == product)
    if outcome == "win":
        filters.append(Trade.net_pnl > 0)
    elif outcome == "loss":
        filters.append(Trade.net_pnl < 0)
    elif outcome == "flat":
        filters.append(Trade.net_pnl == 0)
    if start_date:
        filters.append(Trade.trade_date >= start_date)
    if end_date:
        filters.append(Trade.trade_date <= end_date)
    total = db.scalar(select(func.count(Trade.id)).where(*filters)) or 0
    columns = {
        "trade_date": Trade.trade_date,
        "symbol": Trade.symbol,
        "net_pnl": Trade.net_pnl,
        "return_percent": Trade.return_percent,
        "quantity": Trade.quantity,
    }
    sort_column = columns.get(sort_by, Trade.trade_date)
    order = desc(sort_column) if sort_direction == "desc" else asc(sort_column)
    rows = db.scalars(select(Trade).where(*filters).order_by(order, Trade.id.desc()).offset(offset).limit(limit)).all()
    return {"total": total, "items": [serialize_trade(row) for row in rows]}

