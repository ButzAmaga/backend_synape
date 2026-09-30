"""
Purpose: End-to-end unit and integration test suite verifying Phase 4 session mutations.
Flow:
      1. Test TASK-08: PATCH /api/v1/sessions/{id} title update.
      2. Test TASK-09: PATCH /api/v1/sessions/{id}/category category assignment and validation.
      3. Test TASK-10: POST /api/v1/sessions/{id}/archive and verify mutation shield blocks edits with HTTP 400.
      4. Test TASK-11: DELETE /api/v1/sessions/{id} purges SQLite row and deletes physical audio file from disk.
Inputs: Test AsyncClient and in-memory AsyncSession database handle.
Outputs: Pytest assertion passes.
"""

import os
import pathlib
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import CategoryModel
from app.models.session import SessionModel, SessionStatus

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def sample_category(db_session: AsyncSession) -> CategoryModel:
    """Fixture creating a test category record."""
    category = CategoryModel(
        id="cat-123",
        name="Engineering Syncs",
        color="#3B82F6",
    )
    db_session.add(category)
    await db_session.commit()
    return category


@pytest.fixture
async def sample_session_with_file(db_session: AsyncSession, tmp_path: pathlib.Path) -> SessionModel:
    """Fixture creating a test session with a real temporary audio file on disk."""
    dummy_file = tmp_path / "test_recording.mp3"
    dummy_file.write_bytes(b"MOCK_AUDIO_DATA")

    session = SessionModel(
        id="session-mut-1",
        title="Original Title",
        file_path=str(dummy_file),
        original_file_name="test_recording.mp3",
        file_size_bytes=len(b"MOCK_AUDIO_DATA"),
        mime_type="audio/mpeg",
        status=SessionStatus.INGESTION,
        is_archived=False,
    )
    db_session.add(session)
    await db_session.commit()
    return session


async def test_task08_update_session_title(
    client: AsyncClient, sample_session_with_file: SessionModel
):
    """Verify TASK-08 title update endpoint."""
    response = await client.patch(
        f"/api/v1/sessions/{sample_session_with_file.id}",
        json={"title": "Project Sync"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Project Sync"


async def test_task09_assign_category(
    client: AsyncClient,
    sample_session_with_file: SessionModel,
    sample_category: CategoryModel,
):
    """Verify TASK-09 category foreign key assignment."""
    response = await client.patch(
        f"/api/v1/sessions/{sample_session_with_file.id}/category",
        json={"category_id": sample_category.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category_id"] == sample_category.id


async def test_task10_archive_and_mutation_shield(
    client: AsyncClient, sample_session_with_file: SessionModel
):
    """Verify TASK-10 archiving and mutation shield blocking edits with HTTP 400."""
    # 1. Archive session
    archive_res = await client.post(
        f"/api/v1/sessions/{sample_session_with_file.id}/archive"
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["is_archived"] is True

    # 2. Attempt title mutation on archived record -> Must fail with HTTP 400
    patch_res = await client.patch(
        f"/api/v1/sessions/{sample_session_with_file.id}",
        json={"title": "Blocked Edit Title"},
    )
    assert patch_res.status_code == 400
    error_data = patch_res.json()
    assert "Cannot modify an archived session" in error_data["detail"]


async def test_task11_hard_delete_session(
    client: AsyncClient, sample_session_with_file: SessionModel
):
    """Verify TASK-11 hard deletion purging SQLite record and deleting audio file on disk."""
    file_path = sample_session_with_file.file_path
    assert os.path.exists(file_path) is True

    # Call DELETE endpoint
    delete_res = await client.delete(
        f"/api/v1/sessions/{sample_session_with_file.id}"
    )
    assert delete_res.status_code == 204

    # Confirm physical audio file is deleted from disk
    assert os.path.exists(file_path) is False

    # Confirm record is gone from DB
    get_res = await client.patch(
        f"/api/v1/sessions/{sample_session_with_file.id}",
        json={"title": "Check Existence"},
    )
    assert get_res.status_code == 404