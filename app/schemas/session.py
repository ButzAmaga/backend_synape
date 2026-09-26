"""
Purpose: Defines Pydantic request/response schemas for session resources, including cursor pagination responses.
Flow:
      1. Declare standard SessionResponse DTO schema.
      2. Declare CursorPaginatedSessionResponse schema supporting next cursor pointers and total counts.
Inputs: SessionModel instances or dictionaries.
Outputs: Serialized Pydantic DTOs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.session import SessionStatus


class SessionResponse(BaseModel):
    """
    Purpose: DTO representation of a session record returned to public clients.
    """

    id: str
    title: str
    original_file_name: str
    file_size_bytes: int
    mime_type: str
    status: SessionStatus
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CursorPaginatedSessionResponse(BaseModel):
    """
    Purpose: Response payload wrapper for cursor-paginated session lists.
    Flow:
          1. Hold array of SessionResponse items.
          2. Return opaque base64 string or timestamp string as next_cursor.
          3. Indicate if more items remain available beyond current page.
    Inputs: items list, next_cursor string, has_more boolean.
    Outputs: Cursor paginated response schema.
    """

    items: List[SessionResponse]
    next_cursor: Optional[str] = None
    has_more: bool
    total: int