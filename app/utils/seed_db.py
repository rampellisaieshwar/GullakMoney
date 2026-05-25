from sqlalchemy.orm import Session
from app.models.category_model import Category

DEFAULT_CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Shopping",
    "Travel",
    "Leisure",
    "Other"
]

def seed_default_categories(db: Session):
    for cat_name in DEFAULT_CATEGORIES:
        existing = db.query(Category).filter(
            Category.name == cat_name,
            Category.user_id.is_(None)
        ).first()
        if not existing:
            new_cat = Category(
                name=cat_name,
                user_id=None,
                is_default=True
            )
            db.add(new_cat)
    db.commit()
