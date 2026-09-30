"""
Purpose: Automated testing for Phase 5 pipeline processing, retry endpoint, and startup crash recovery.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionModel
from app.schemas.pipeline import PipelineStatus
from app.core.pipeline import reset_stale_processing_tasks


@pytest.mark.asyncio
async def test_startup_crash_recovery_resets_stale_sessions(db_session: AsyncSession):
    """
    Tests that interrupted tasks in INGESTION, CONVERSION, or SYNTHESIS are reset to FAILED on startup.
    """
    stale_session = SessionModel(
        id="stale-test-session-id",
        title="Stale Session",
        file_path="/tmp/stale.mp3",
        status=PipelineStatus.CONVERSION.value,
    )
    db_session.add(stale_session)
    await db_session.commit()

    reset_count = await reset_stale_processing_tasks()
    assert reset_count >= 1

    await db_session.refresh(stale_session)
    assert stale_session.status == PipelineStatus.FAILED.value
    assert stale_session.error_message == "Process interrupted by system restart."


@pytest.mark.asyncio
async def test_retry_failed_session_endpoint(client: AsyncClient, db_session: AsyncSession):
    """
    Tests retry processing endpoint on a failed session.
    """
    failed_session = SessionModel(
        id="failed-session-id",
        title="Failed Session Test",
        file_path="/tmp/failed.mp3",
        status=PipelineStatus.FAILED.value,
        error_message="Previous error",
    )
    db_session.add(failed_session)
    await db_session.commit()

    response = await client.post("/api/v1/sessions/failed-session-id/retry")
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == PipelineStatus.INGESTION.value