"""
Purpose: Defines Pydantic request/response schemas for session resources and mutation requests.
Flow:
      1. Declare SessionResponse DTO schema.
      2. Declare SessionUpdateRequest and CategoryAssignmentRequest mutation schemas.
      3. Declare CursorPaginatedSessionResponse list schema.
Inputs: Field values, session models, or dictionaries.
Outputs: Serialized and validated Pydantic DTOs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
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
    category_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionUpdateRequest(BaseModel):
    """
    Purpose: Schema for title update mutations on existing sessions.
    Flow:
          1. Validate title string length between 1 and 255 characters.
    Inputs: title (str).
    Outputs: Validated title payload.
    """

    title: str = Field(..., min_length=1, max_length=255, description="Updated session title")


class CategoryAssignmentRequest(BaseModel):
    """
    Purpose: Schema for assigning or unassigning a category to a session.
    Flow:
          1. Accept optional category_id string or None to unassign.
    Inputs: category_id (Optional[str]).
    Outputs: Validated category assignment payload.
    """

    category_id: Optional[str] = Field(
        None, description="Category UUID string to assign, or null to clear"
    )


class CursorPaginatedSessionResponse(BaseModel):
    """
    Purpose: Response payload wrapper for cursor-paginated session lists.
    """

    items: List[SessionResponse]
    next_cursor: Optional[str] = None
    has_more: bool
    total: int