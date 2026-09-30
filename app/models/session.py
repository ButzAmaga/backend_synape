"""
Purpose: Defines SQLAlchemy ORM domain model for meeting sessions table in SQLite.
Flow:
      1. Declare SessionStatus enumeration for pipeline states.
      2. Model SessionModel database fields including foreign key to CategoryModel and error_message.
      3. Establish database table structure for session persistence.
Inputs: DeclarativeBase from app.core.database.
Outputs: SessionModel SQLAlchemy entity.
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import CategoryModel


class SessionStatus(str, enum.Enum):
    """
    Purpose: Enumerates all valid processing states for a meeting session.
    Flow:
          1. Define explicit string constant values for pipeline stages.
    Inputs: None.
    Outputs: SessionStatus enum values.
    """

    INGESTION = "INGESTION"
    CONVERSION = "CONVERSION"
    SYNTHESIS = "SYNTHESIS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SessionModel(Base):
    """
    Purpose: Map session database record to SQLite "sessions" table schema.
    Flow:
          1. Set table name to "sessions".
          2. Map primary key UUID string.
          3. Map file metadata, category foreign key, status, error details, archive flags, and timestamps.
    Inputs: Base ORM declarative class.
    Outputs: Mapped ORM model for session operations.
    """

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        default=SessionStatus.INGESTION,
        nullable=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    category: Mapped[Optional["CategoryModel"]] = relationship(
        "CategoryModel", back_populates="sessions"
    )