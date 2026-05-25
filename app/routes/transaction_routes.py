from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status
)
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Literal
from datetime import datetime
from app.core.database import get_db
from app.models.transaction_model import Transaction
from app.models.category_model import Category
from app.models.user_model import User
from app.schemas.transaction_schema import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate
)
from app.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate category exists for this user (either system/default or custom)
    category_exists = db.query(Category).filter(
        func.lower(Category.name) == func.lower(transaction.category),
        (Category.user_id.is_(None) | (Category.user_id == current_user.id))
    ).first()
    if not category_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{transaction.category}' is not a valid default or custom category."
        )

    # Use specified date or current time if not provided
    transaction_date = transaction.date if transaction.date is not None else datetime.utcnow()

    new_transaction = Transaction(
        amount=transaction.amount,
        type=transaction.type,
        category=category_exists.name,  # Save the canonical name
        date=transaction_date,
        note=transaction.note,
        user_id=current_user.id
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@router.get(
    "/",
    response_model=list[TransactionResponse]
)
def get_transactions(
    page: int = 1,
    limit: int = 10,
    type: Optional[Literal["income", "expense"]] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sort_by: Optional[Literal["date", "amount"]] = "date",
    order: Optional[Literal["asc", "desc"]] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure page is at least 1, limit at least 1
    page = max(1, page)
    limit = max(1, limit)

    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    # Filter by type
    if type:
        query = query.filter(Transaction.type == type)

    # Filter by category name
    if category:
        query = query.filter(func.lower(Transaction.category) == func.lower(category))

    # Filter by date range
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    # Determine sorting
    sort_column = Transaction.date if sort_by == "date" else Transaction.amount
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination skip/limit
    skip = (page - 1) * limit
    transactions = query.offset(skip).limit(limit).all()
    return transactions

@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction

@router.patch(
    "/{transaction_id}",
    response_model=TransactionResponse
)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Partial update using Pydantic dumps
    update_data = transaction_update.model_dump(exclude_unset=True)

    if "category" in update_data:
        category_name = update_data["category"]
        category_exists = db.query(Category).filter(
            func.lower(Category.name) == func.lower(category_name),
            (Category.user_id.is_(None) | (Category.user_id == current_user.id))
        ).first()
        if not category_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_name}' is not a valid default or custom category."
            )
        update_data["category"] = category_exists.name

    for key, value in update_data.items():
        setattr(transaction, key, value)

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
