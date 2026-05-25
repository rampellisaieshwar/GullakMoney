from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None

class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)
