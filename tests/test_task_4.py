"""
Purpose: Validates Task 4 POST /api/v1/sessions upload endpoint behavior.
Flow:
      1. Test successful multipart audio upload stream and 201 response.
      2. Test rejection of unsupported file MIME types (HTTP 400).
Inputs: client (AsyncClient fixture).
Outputs: Pytest assertions.
"""

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session_success(client: AsyncClient):
    """
    Purpose: Verify valid audio file upload creates a database session entry.
    Flow:
          1. Create mock audio file byte buffer.
          2. Send POST request with multipart form data to /api/v1/sessions.
          3. Assert response HTTP status 201 Created and correct schema structure.
    """
    fake_audio = io.BytesIO(b"ID3" + b"\x00" * 1000)
    files = {"file": ("test_recording.mp3", fake_audio, "audio/mpeg")}
    data = {"title": "Weekly Engineering Sync"}

    response = await client.post("/api/v1/sessions", data=data, files=files)

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Weekly Engineering Sync"
    assert payload["status"] == "INGESTION"
    assert payload["original_file_name"] == "test_recording.mp3"


@pytest.mark.asyncio
async def test_create_session_invalid_mime_type(client: AsyncClient):
    """
    Purpose: Verify endpoint rejects non-audio file formats.
    Flow:
          1. Send POST request with text/plain file payload.
          2. Assert HTTP 400 Bad Request error.
    """
    fake_text = io.BytesIO(b"This is a text document, not an audio file.")
    files = {"file": ("notes.txt", fake_text, "text/plain")}
    data = {"title": "Invalid Document"}

    response = await client.post("/api/v1/sessions", data=data, files=files)

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]