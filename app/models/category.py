"""
Purpose: Defines SQLAlchemy ORM domain model for categories in SQLite.
Flow:
      1. Define CategoryModel database fields.
      2. Map relationship to SessionModel.
Inputs: DeclarativeBase from app.core.database.
Outputs: CategoryModel SQLAlchemy entity.
"""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import SessionModel


class CategoryModel(Base):
    """
    Purpose: Map category database record to SQLite "categories" table schema.
    Flow:
          1. Set table name to "categories".
          2. Map primary key string ID and name.
          3. Establish one-to-many relationship with SessionModel.
    Inputs: Base ORM declarative class.
    Outputs: Mapped ORM model for category operations.
    """

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(30), default="#6B7280", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    sessions: Mapped[List["SessionModel"]] = relationship(
        "SessionModel", back_populates="category"
    )