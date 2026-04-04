from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from db import get_db
from models.record import Record, TypeEnum
from models.user import User
from dependencies.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Returns total income, total expense, and net balance."""
    results = (
        db.query(Record.type, func.sum(Record.amount).label("total"))
        .group_by(Record.type)
        .all()
    )

    totals = {row.type: row.total for row in results}
    total_income = totals.get(TypeEnum.income, 0.0) or 0.0
    total_expense = totals.get(TypeEnum.expense, 0.0) or 0.0

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(total_income - total_expense, 2),
    }


@router.get("/categories")
def get_category_totals(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Returns total amount grouped by category and type."""
    results = (
        db.query(Record.category, Record.type, func.sum(Record.amount).label("total"))
        .group_by(Record.category, Record.type)
        .all()
    )

    data = [
        {"category": row.category, "type": row.type, "total": round(row.total, 2)}
        for row in results
    ]
    return {"categories": data}


@router.get("/trends")
def get_monthly_trends(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Returns monthly income and expense totals for trend analysis."""
    results = (
        db.query(
            extract("year", Record.date).label("year"),
            extract("month", Record.date).label("month"),
            Record.type,
            func.sum(Record.amount).label("total"),
        )
        .group_by("year", "month", Record.type)
        .order_by("year", "month")
        .all()
    )

    from collections import defaultdict
    trends = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for row in results:
        key = f"{int(row.year)}-{int(row.month):02d}"
        trends[key][row.type] = round(row.total, 2)

    return {
        "trends": [
            {"month": k, "income": v["income"], "expense": v["expense"]}
            for k, v in sorted(trends.items())
        ]
    }


@router.get("/recent")
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Returns the most recent N records as a summary (no raw record IDs exposed to viewer)."""
    records = (
        db.query(Record)
        .order_by(Record.date.desc(), Record.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "recent": [
            {
                "date": str(r.date),
                "type": r.type,
                "category": r.category,
                "amount": r.amount,
            }
            for r in records
        ]
    }
