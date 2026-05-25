from pydantic import BaseModel
from typing import List

class FinancialSummary(BaseModel):
    income: float
    expenses: float
    balance: float

class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float

class MonthlyTrend(BaseModel):
    month: str
    income: float
    expense: float
