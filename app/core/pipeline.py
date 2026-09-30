"""
Purpose: Concurrency management, status progression state machine, and startup recovery for the processing pipeline.
"""

import asyncio
import logging
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.session import SessionModel
from app.schemas.pipeline import PipelineStatus

logger = logging.getLogger("api.pipeline")

# Bounded concurrency lock (max 2 parallel processing jobs)
processing_semaphore = asyncio.Semaphore(2)


async def transition_session_status(
    db: AsyncSession,
    session_id: str,
    new_status: PipelineStatus,
    error_message: str | None = None,
) -> None:
    """
    Purpose: Atomically updates session status and optional error message in database.
    """
    values = {"status": new_status.value}
    if error_message is not None:
        values["error_message"] = error_message

    stmt = (
        update(SessionModel)
        .where(SessionModel.id == session_id)
        .values(**values)
    )
    await db.execute(stmt)
    await db.commit()


async def reset_stale_processing_tasks() -> int:
    """
    Purpose: Startup crash-recovery handler resetting interrupted in-flight tasks to FAILED state.
    """
    active_statuses = [
        PipelineStatus.INGESTION.value,
        PipelineStatus.CONVERSION.value,
        PipelineStatus.SYNTHESIS.value,
    ]
    async with async_session_factory() as db:
        stmt = (
            update(SessionModel)
            .where(SessionModel.status.in_(active_statuses))
            .values(
                status=PipelineStatus.FAILED.value,
                error_message="Process interrupted by system restart.",
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        affected_count = result.rowcount
        if affected_count > 0:
            logger.warning(
                f"Startup crash recovery: reset {affected_count} interrupted processing tasks to FAILED."
            )
        return affected_count