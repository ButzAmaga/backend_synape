"""
Purpose: Enhanced session repository containing date-descending cursor pagination query logic filtering non-archived entries.
Flow:
      1. Accept optional base64 cursor decoding to ISO timestamp.
      2. Filter entries where is_archived == False and created_at < cursor_timestamp.
      3. Fetch limit + 1 records to accurately determine has_more boolean.
Inputs: AsyncSession database handle.
Outputs: Tuple of (records, next_cursor, has_more, total_count).
"""

import base64
from datetime import datetime
from typing import Sequence, Tuple, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import SessionModel


class SessionRepository:
    """
    Purpose: Encapsulates data access and cursor-paginated queries for session entities.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: SessionModel) -> SessionModel:
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: str) -> Optional[SessionModel]:
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_all_paginated(
        self,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[Sequence[SessionModel], Optional[str], bool, int]:
        """
        Purpose: Fetches non-archived sessions ordered by creation date descending with cursor pagination.
        Flow:
              1. Count total non-archived records.
              2. Decode cursor string to datetime if provided.
              3. Query limit + 1 items with created_at < cursor filter.
              4. Derive next_cursor and has_more flag.
        Inputs: cursor (Optional[str]), limit (int).
        Outputs: Tuple containing (items, next_cursor, has_more, total_count).
        """
        # Count total non-archived sessions
        total_stmt = select(func.count(SessionModel.id)).where(
            SessionModel.is_archived == False
        )
        total_res = await self.db.execute(total_stmt)
        total_count = total_res.scalar_one() or 0

        # Base query for non-archived items ordered descending by created_at
        stmt = (
            select(SessionModel)
            .where(SessionModel.is_archived == False)
            .order_by(SessionModel.created_at.desc(), SessionModel.id.desc())
        )

        if cursor:
            try:
                decoded_str = base64.b64decode(cursor.encode()).decode()
                cursor_dt = datetime.fromisoformat(decoded_str)
                stmt = stmt.where(SessionModel.created_at < cursor_dt)
            except Exception:
                pass  # Ignore invalid cursor formatting gracefully

        # Query limit + 1 to determine if more items exist
        stmt = stmt.limit(limit + 1)
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        has_more = len(records) > limit
        items = records[:limit]

        next_cursor = None
        if has_more and items:
            last_item_dt = items[-1].created_at.isoformat()
            next_cursor = base64.b64encode(last_item_dt.encode()).decode()

        return items, next_cursor, has_more, total_count