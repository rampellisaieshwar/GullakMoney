from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.transaction_model import Transaction
from app.models.user_model import User
from app.schemas.analytics_schema import (
    FinancialSummary,
    CategoryBreakdown,
    MonthlyTrend
)
from app.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

@router.get("/summary", response_model=FinancialSummary)
def get_financial_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total income query
    income_query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "income"
    )
    if start_date:
        income_query = income_query.filter(Transaction.date >= start_date)
    if end_date:
        income_query = income_query.filter(Transaction.date <= end_date)
    income_val = income_query.scalar() or 0.0

    # Total expenses query
    expense_query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense"
    )
    if start_date:
        expense_query = expense_query.filter(Transaction.date >= start_date)
    if end_date:
        expense_query = expense_query.filter(Transaction.date <= end_date)
    expense_val = expense_query.scalar() or 0.0

    return {
        "income": income_val,
        "expenses": expense_val,
        "balance": income_val - expense_val
    }

@router.get("/categories", response_model=list[CategoryBreakdown])
def get_category_breakdown(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total expenses for percentage calculation
    total_expenses_query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense"
    )
    if start_date:
        total_expenses_query = total_expenses_query.filter(Transaction.date >= start_date)
    if end_date:
        total_expenses_query = total_expenses_query.filter(Transaction.date <= end_date)
    total_expenses = total_expenses_query.scalar() or 0.0

    # Group expenses by category
    category_sums_query = db.query(
        Transaction.category,
        func.sum(Transaction.amount).label("amount")
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense"
    )
    if start_date:
        category_sums_query = category_sums_query.filter(Transaction.date >= start_date)
    if end_date:
        category_sums_query = category_sums_query.filter(Transaction.date <= end_date)
    
    category_sums = category_sums_query.group_by(Transaction.category).all()

    breakdown = []
    for cat_name, amt in category_sums:
        percentage = (amt / total_expenses * 100) if total_expenses > 0 else 0.0
        breakdown.append({
            "category": cat_name,
            "amount": amt,
            "percentage": round(percentage, 2)
        })
    # Sort by amount descending
    breakdown.sort(key=lambda x: x["amount"], reverse=True)
    return breakdown

@router.get("/monthly", response_model=list[MonthlyTrend])
def get_monthly_trends(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if months <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Months parameter must be greater than 0."
        )

    today = datetime.utcnow()
    # Go back to start of month that is (months - 1) ago
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    start_date = datetime(year, month, 1)

    # Perform DB aggregation grouped by month using PostgreSQL to_char
    results = db.query(
        func.to_char(Transaction.date, "YYYY-MM").label("month"),
        func.coalesce(func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)), 0).label("income"),
        func.coalesce(func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)), 0).label("expense")
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date
    ).group_by(
        "month"
    ).order_by(
        "month"
    ).all()

    trends = []
    for row in results:
        trends.append({
            "month": row.month,
            "income": float(row.income),
            "expense": float(row.expense)
        })
    return trends
