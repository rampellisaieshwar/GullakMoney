from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.category_model import Category
from app.models.transaction_model import Transaction
from app.models.user_model import User
from app.schemas.category_schema import CategoryCreate, CategoryUpdate, CategoryResponse
from app.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).filter(
        (Category.user_id.is_(None)) | (Category.user_id == current_user.id)
    ).all()
    return categories

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if category already exists for user (either default or user's custom)
    existing = db.query(Category).filter(
        func.lower(Category.name) == func.lower(category_data.name),
        (Category.user_id.is_(None) | (Category.user_id == current_user.id))
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists."
        )
        
    new_category = Category(
        name=category_data.name,
        user_id=current_user.id,
        is_default=False
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
        
    if category.user_id is None or category.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default categories cannot be updated."
        )
        
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
        
    # Check if the new name clashes with another category (either default or user's custom)
    existing = db.query(Category).filter(
        func.lower(Category.name) == func.lower(category_data.name),
        (Category.user_id.is_(None) | (Category.user_id == current_user.id)),
        Category.id != category_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Another category with this name already exists."
        )
        
    old_name = category.name
    new_name = category_data.name
    
    # Update category name
    category.name = new_name
    db.add(category)
    
    # Update transactions referencing the old category string
    db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.category == old_name
    ).update({Transaction.category: new_name})
    
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
        
    if category.user_id is None or category.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default categories cannot be deleted."
        )
        
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
        
    # Check if the category is in use by transactions
    in_use = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.category == category.name
    ).first()
    
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category because it is in use by transactions. Please reassign or delete those transactions first."
        )
        
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
