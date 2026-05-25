from pydantic import BaseModel, Field
from typing import Optional

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class CategoryResponse(BaseModel):
    id: int
    name: str
    user_id: Optional[int] = None
    is_default: bool

    class Config:
        from_attributes = True
