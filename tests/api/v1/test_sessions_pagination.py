import pytest
import base64
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionModel, SessionStatus

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def sample_sessions(db_session: AsyncSession):
    """
    Fixture that populates the database with test sessions with staggered creation dates.
    """
    now = datetime.utcnow()
    sessions = [
        SessionModel(
            id=f"session-id-{i}",
            title=f"Session {i}",
            file_path=f"/.synapse/audio/session-id-{i}.mp3",
            original_file_name=f"recording_{i}.mp3",
            file_size_bytes=1024 * (i + 1),
            mime_type="audio/mpeg",
            status=SessionStatus.INGESTION,
            is_archived=(i == 4),  # Mark Session 4 as archived
            created_at=now - timedelta(minutes=i * 10),
        )
        for i in range(5)
    ]
    db_session.add_all(sessions)
    await db_session.commit()
    return sessions


async def test_list_sessions_default_pagination(client: AsyncClient, sample_sessions):
    """
    Test retrieving sessions with default parameters (limit=20).
    Excludes archived sessions (Session 4).
    """
    response = await client.get("/api/v1/sessions")
    
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "has_more" in data
    assert "total" in data
    
    # 5 total sessions minus 1 archived = 4 active
    assert data["total"] == 4
    assert len(data["items"]) == 4
    assert data["has_more"] is False
    assert data["next_cursor"] is None

    # Check descending order by created_at
    titles = [item["title"] for item in data["items"]]
    assert titles == ["Session 0", "Session 1", "Session 2", "Session 3"]


async def test_list_sessions_custom_limit(client: AsyncClient, sample_sessions):
    """
    Test cursor pagination with limit=2.
    """
    response = await client.get("/api/v1/sessions?limit=2")
    
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 2
    assert data["has_more"] is True
    assert data["total"] == 4
    assert data["next_cursor"] is not None

    # Verify next_cursor is a valid base64 encoded ISO timestamp
    decoded_cursor = base64.b64decode(data["next_cursor"].encode()).decode()
    assert datetime.fromisoformat(decoded_cursor)


async def test_list_sessions_cursor_traversal(client: AsyncClient, sample_sessions):
    """
    Test step-by-step cursor traversal across multiple pages.
    """
    # Page 1
    res_page1 = await client.get("/api/v1/sessions?limit=2")
    data1 = res_page1.json()
    assert len(data1["items"]) == 2
    assert [item["title"] for item in data1["items"]] == ["Session 0", "Session 1"]
    
    cursor = data1["next_cursor"]
    assert cursor is not None

    # Page 2 using cursor
    res_page2 = await client.get(f"/api/v1/sessions?limit=2&cursor={cursor}")
    data2 = res_page2.json()
    assert len(data2["items"]) == 2
    assert [item["title"] for item in data2["items"]] == ["Session 2", "Session 3"]
    assert data2["has_more"] is False
    assert data2["next_cursor"] is None


async def test_list_sessions_invalid_limit_bounds(client: AsyncClient):
    """
    Test validation errors when limit is < 1 or > 100.
    """
    # Test limit=0
    res_zero = await client.get("/api/v1/sessions?limit=0")
    assert res_zero.status_code == 422  # Unprocessable Entity (FastAPI validation)

    # Test limit=101
    res_over = await client.get("/api/v1/sessions?limit=101")
    assert res_over.status_code == 422


async def test_list_sessions_malformed_cursor_graceful_recovery(
    client: AsyncClient, sample_sessions
):
    """
    Test that supplying a malformed non-base64 cursor string fails gracefully and returns initial page.
    """
    response = await client.get("/api/v1/sessions?cursor=invalid_base64_string!!!")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 4