from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user_model import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.schemas.user_schema import (
    UserRegister,
    UserResponse,
    UserLogin,
    TokenResponse
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    is_password_valid = verify_password(
        user.password,
        existing_user.hashed_password
    )
    if not is_password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    access_token = create_access_token(
        data={
            "sub": str(existing_user.id)
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully. Please discard your authentication token."}

