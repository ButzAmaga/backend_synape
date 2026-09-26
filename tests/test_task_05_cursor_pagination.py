"""
Purpose: Unit tests for TASK-05 JIT cursor pagination query helpers against SQLite database.
Flow:
      1. Seed mock session entities across varying timestamps.
      2. Verify first page query returns expected limit and correct next_cursor.
      3. Verify subsequent page query using returned cursor filters older entries.
      4. Ensure archived session records are excluded.
Inputs: db_session AsyncSession fixture.
Outputs: Pytest assertions.
"""

import uuid
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionModel, SessionStatus
from app.repositories.session_repository import SessionRepository


@pytest.mark.asyncio
async def test_cursor_pagination_filtering_and_ordering(db_session: AsyncSession):
    """
    Purpose: Verify date-descending cursor pagination logic and non-archived filtering.
    Flow:
          1. Create 5 session entities with different creation dates (1 is archived).
          2. Fetch page 1 with limit=2.
          3. Validate order (newest first), has_more=True, and valid next_cursor.
          4. Fetch page 2 with returned cursor.
          5. Confirm archived record is excluded from total and items.
    """
    repo = SessionRepository(db_session)
    base_time = datetime.utcnow()

    # Create 4 active sessions and 1 archived session
    sessions = []
    for i in range(4):
        s = SessionModel(
            id=str(uuid.uuid4()),
            title=f"Session {i}",
            file_path=f"/tmp/audio_{i}.m4a",
            original_file_name=f"recording_{i}.m4a",
            file_size_bytes=1000 * (i + 1),
            mime_type="audio/m4a",
            status=SessionStatus.COMPLETED,
            is_archived=False,
            created_at=base_time - timedelta(hours=i),
        )
        sessions.append(s)
        db_session.add(s)

    archived_s = SessionModel(
        id=str(uuid.uuid4()),
        title="Archived Session",
        file_path="/tmp/audio_archived.m4a",
        original_file_name="archived.m4a",
        file_size_bytes=5000,
        mime_type="audio/m4a",
        status=SessionStatus.COMPLETED,
        is_archived=True,
        created_at=base_time + timedelta(hours=1),
    )
    db_session.add(archived_s)
    await db_session.commit()

    # --- Page 1 Execution ---
    items_p1, next_cursor_p1, has_more_p1, total = await repo.get_all_paginated(
        cursor=None, limit=2
    )

    assert total == 4  # Excludes archived record
    assert len(items_p1) == 2
    assert has_more_p1 is True
    assert next_cursor_p1 is not None
    assert items_p1[0].title == "Session 0"  # Newest
    assert items_p1[1].title == "Session 1"

    # --- Page 2 Execution ---
    items_p2, next_cursor_p2, has_more_p2, _ = await repo.get_all_paginated(
        cursor=next_cursor_p1, limit=2
    )

    assert len(items_p2) == 2
    assert items_p2[0].title == "Session 2"
    assert items_p2[1].title == "Session 3"  # Oldest
    assert has_more_p2 is False
    assert next_cursor_p2 is None