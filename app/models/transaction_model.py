from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    note = Column(String)
    date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )
    
    user = relationship("User")

