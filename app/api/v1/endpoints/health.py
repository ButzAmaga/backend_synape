"""
Purpose: Provides API controller endpoint for verifying database connectivity and disk readiness.
Flow:
      1. Accept HTTP GET requests at /health.
      2. Ping SQLite database using text("SELECT 1") query.
      3. Evaluate available host disk space metrics via shutil.disk_usage.
      4. Assemble and return HealthCheckResponse schema.
Inputs: AsyncSession context dependency from database connection pool.
Outputs: HealthCheckResponse payload with HTTP 200 OK or 503 Service Unavailable.
"""

import shutil
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check backend operational status",
)
async def check_health(
    response: Response, db: AsyncSession = Depends(get_db)
) -> HealthCheckResponse:
    """
    Purpose: Evaluates active database connectivity and disk storage capacity.
    Flow:
          1. Issue SELECT 1 test query to active SQLite async session.
          2. Compute host filesystem storage metrics using shutil.disk_usage.
          3. Set HTTP status code to 503 if database connection fails.
          4. Return HealthCheckResponse instance.
    Inputs: Response handle and active AsyncSession dependency instance.
    Outputs: HealthCheckResponse instance indicating operational health.
    """
    db_healthy = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    disk_usage = shutil.disk_usage(settings.BASE_DATA_DIR)

    return HealthCheckResponse(
        status="HEALTHY" if db_healthy else "UNHEALTHY",
        database_connected=db_healthy,
        disk_free_bytes=disk_usage.free,
        disk_total_bytes=disk_usage.total,
    )