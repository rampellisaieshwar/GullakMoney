from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.dependencies import get_current_user
from app.models.user_model import User
from app.core.database import get_db
from app.core.security import verify_password, hash_password
from app.schemas.user_schema import UserUpdate, ChangePassword, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_update.name is not None:
        current_user.name = user_update.name
    
    if user_update.email is not None and user_update.email != current_user.email:
        # Check if the email is already in use
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_update.email

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/change-password")
def change_password(
    password_data: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Hash and save new password
    current_user.hashed_password = hash_password(password_data.new_password)
    db.add(current_user)
    db.commit()
    return {"message": "Password changed successfully"}
