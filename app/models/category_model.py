from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, UniqueConstraint
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_default = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='_category_name_user_uc'),
    )
