from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from db import get_db
from models.record import Record
from models.user import User
from enums import TypeEnum
from dependencies.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Reusable filter expression — keeps all dashboard queries consistent
# with the soft-delete pattern used in records.py
_NOT_DELETED = Record.is_deleted == False  # noqa: E712


@router.get("/summary", summary="Overall financial summary (All roles)")
def get_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    Returns total income, total expenses, and net balance across all active records.
    Available to all authenticated users (viewer, analyst, admin).
    """
    results = (
        db.query(Record.type, func.sum(Record.amount).label("total"))
        .filter(_NOT_DELETED)
        .group_by(Record.type)
        .all()
    )

    totals = {row.type: row.total for row in results}
    # Convert Decimal → float for JSON-serialisable output;
    # rounding to 2 dp mirrors standard financial display conventions
    total_income = float(totals.get(TypeEnum.income, 0) or 0)
    total_expense = float(totals.get(TypeEnum.expense, 0) or 0)

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(total_income - total_expense, 2),
    }


@router.get("/categories", summary="Category-wise totals (All roles)")
def get_category_totals(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    Returns total amount grouped by category and type.
    Useful for pie/bar charts on the dashboard.
    """
    results = (
        db.query(
            Record.category,
            Record.type,
            func.sum(Record.amount).label("total"),
        )
        .filter(_NOT_DELETED)
        .group_by(Record.category, Record.type)
        .all()
    )

    return {
        "categories": [
            {
                "category": row.category,
                "type": row.type,
                "total": round(float(row.total), 2),
            }
            for row in results
        ]
    }


@router.get("/trends", summary="Monthly income/expense trends (All roles)")
def get_monthly_trends(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    Returns monthly income and expense totals ordered chronologically.
    Designed for line/area chart trend visualisations.
    """
    results = (
        db.query(
            extract("year", Record.date).label("year"),
            extract("month", Record.date).label("month"),
            Record.type,
            func.sum(Record.amount).label("total"),
        )
        .filter(_NOT_DELETED)
        .group_by("year", "month", Record.type)
        .order_by("year", "month")
        .all()
    )

    trends = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for row in results:
        key = f"{int(row.year)}-{int(row.month):02d}"
        trends[key][row.type] = round(float(row.total), 2)

    return {
        "trends": [
            {"month": k, "income": v["income"], "expense": v["expense"]}
            for k, v in sorted(trends.items())
        ]
    }


@router.get("/recent", summary="Recent financial activity (All roles)")
def get_recent_activity(
    limit: int = Query(10, ge=1, le=100, description="Number of recent records (max 100)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Returns the most recent N active records as a lightweight summary.
    Raw record IDs are intentionally excluded — viewers get data without
    being able to construct direct record URLs.
    """
    records = (
        db.query(Record)
        .filter(_NOT_DELETED)
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
                "amount": float(r.amount),
            }
            for r in records
        ]
    }
