"""
Purpose: Enhanced session repository with pagination and full mutation operations.
Flow:
      1. Provide methods for create, read, update title/category, archive, and delete.
Inputs: AsyncSession database handle.
Outputs: SessionModel entities, pagination tuples, or booleans.
"""

import base64
from datetime import datetime
from typing import Sequence, Tuple, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import SessionModel


class SessionRepository:
    """
    Purpose: Encapsulates data access and mutations for session entities.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: SessionModel) -> SessionModel:
        """
        Purpose: Persists a new session record into SQLite.
        Flow:
              1. Add model to session context, flush, and refresh.
        Inputs: session (SessionModel).
        Outputs: SessionModel instance.
        """
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: str) -> Optional[SessionModel]:
        """
        Purpose: Retrieves session record by ID.
        Flow:
              1. Execute SELECT query on sessions table matching session_id.
        Inputs: session_id (str).
        Outputs: SessionModel or None.
        """
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_title(self, session_id: str, title: str) -> Optional[SessionModel]:
        """
        Purpose: Updates session title and refreshes updated_at timestamp.
        Flow:
              1. Query session by ID.
              2. Apply title update and commit transaction.
        Inputs: session_id (str), title (str).
        Outputs: Updated SessionModel or None.
        """
        session = await self.get_by_id(session_id)
        if not session:
            return None
        session.title = title
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update_category(
        self, session_id: str, category_id: Optional[str]
    ) -> Optional[SessionModel]:
        """
        Purpose: Updates category foreign key association on a session.
        Flow:
              1. Query session by ID.
              2. Assign category_id and commit transaction.
        Inputs: session_id (str), category_id (Optional[str]).
        Outputs: Updated SessionModel or None.
        """
        session = await self.get_by_id(session_id)
        if not session:
            return None
        session.category_id = category_id
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def set_archived(self, session_id: str, is_archived: bool) -> Optional[SessionModel]:
        """
        Purpose: Sets session archived flag.
        Flow:
              1. Query session by ID.
              2. Update is_archived state and commit transaction.
        Inputs: session_id (str), is_archived (bool).
        Outputs: Updated SessionModel or None.
        """
        session = await self.get_by_id(session_id)
        if not session:
            return None
        session.is_archived = is_archived
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete(self, session_id: str) -> bool:
        """
        Purpose: Hard deletes a session record from SQLite database.
        Flow:
              1. Fetch session by ID.
              2. Delete record from database and commit transaction.
        Inputs: session_id (str).
        Outputs: Boolean True if deleted, False if not found.
        """
        session = await self.get_by_id(session_id)
        if not session:
            return False
        await self.db.delete(session)
        await self.db.commit()
        return True

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
        total_stmt = select(func.count(SessionModel.id)).where(
            SessionModel.is_archived == False
        )
        total_res = await self.db.execute(total_stmt)
        total_count = total_res.scalar_one() or 0

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
                pass

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