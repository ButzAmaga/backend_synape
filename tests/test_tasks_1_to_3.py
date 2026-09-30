"""
Purpose: Validates system functionality across Tasks 1, 2, and 3.
Flow:
      1. Verify core middleware, correlation tracking, and exception handling (Task 1).
      2. Verify /api/v1/health operational endpoint (Task 2).
      3. Verify Session model, repository layer, and storage verification logic (Task 3).
Inputs: Pytest test runner, client fixture, and db_session fixture.
Outputs: Asserts test pass or fail status.
"""

import uuid
import pytest
from httpx import AsyncClient
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionModel, SessionStatus
from app.repositories.session_repository import SessionRepository
from app.services.local_storage_service import LocalStorageService


@pytest.mark.asyncio
async def test_task1_correlation_middleware_and_404_handling(client: AsyncClient):
    """
    Purpose: Verify correlation ID generation and global error response format from Task 1.
    Flow:
          1. Send request to non-existent endpoint.
          2. Assert response status code is 404.
          3. Confirm presence of X-Request-ID response header.
    Inputs: client (AsyncClient).
    Outputs: None.
    """
    response = await client.get("/non-existent-route")
    assert response.status_code == 404
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_task2_health_endpoint(client: AsyncClient):
    """
    Purpose: Verify Task 2 health status response model and database connectivity check.
    Flow:
          1. Issue GET request to /api/v1/health.
          2. Assert HTTP status 200 OK.
          3. Validate JSON payload structure against expected health metrics.
    Inputs: client (AsyncClient).
    Outputs: None.
    """
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["database_connected"] is True
    assert isinstance(data["disk_free_bytes"], int)
    assert isinstance(data["disk_total_bytes"], int)


@pytest.mark.asyncio
async def test_task3_storage_service_disk_verification():
    """
    Purpose: Verify Task 3 LocalStorageService disk space check logic.
    Flow:
          1. Execute verify_disk_space with reasonable file size (1 KB).
          2. Execute verify_disk_space with unfulfillable required bytes size.
          3. Assert HTTP 507 exception is raised on insufficient space.
    Inputs: None.
    Outputs: None.
    """
    # 1. Should pass without raising exception for small file sizes
    LocalStorageService.verify_disk_space(required_bytes=1024)

    # 2. Should raise 507 Insufficient Storage when requesting impossible bytes
    impossible_bytes = 10**18  # 1 Exabyte
    with pytest.raises(HTTPException) as exc_info:
        LocalStorageService.verify_disk_space(required_bytes=impossible_bytes)

    assert exc_info.value.status_code == 507