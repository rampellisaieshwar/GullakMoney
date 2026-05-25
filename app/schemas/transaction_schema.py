from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    type: Literal["income", "expense"]
    category: str = Field(..., min_length=1)
    date: Optional[datetime] = None
    note: Optional[str] = None

class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[Literal["income", "expense"]] = None
    category: Optional[str] = Field(None, min_length=1)
    date: Optional[datetime] = None
    note: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    note: Optional[str]
    date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
