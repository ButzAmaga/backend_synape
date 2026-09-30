"""
Purpose: Asynchronous pipeline processing service (Whisper v3 Conversion & AI Synthesis).
"""

import asyncio
import logging
from app.core.database import async_session_factory
from app.core.pipeline import processing_semaphore, transition_session_status
from app.models.session import SessionModel
from app.schemas.pipeline import PipelineStatus
from app.repositories.session_repository import SessionRepository

logger = logging.getLogger("api.pipeline_service")

STAGE_TIMEOUT_SECONDS = 300.0  # 5 minutes per pipeline stage


class AudioProcessorService:
    """
    Purpose: Orchestrates Phase 02 (Conversion) and Phase 03 (Synthesis) background tasks.
    """

    @classmethod
    async def process_session(cls, session_id: str) -> None:
        """
        Purpose: Orchestrates 3-phase asynchronous workflow lifecycle under semaphore throttling.
        """
        async with processing_semaphore:
            async with async_session_factory() as db:
                repo = SessionRepository(db)
                session = await repo.get_by_id(session_id)
                if not session or session.status == PipelineStatus.COMPLETED.value:
                    return

                try:
                    # Stage 1: Transition to CONVERSION (Speech-to-Text)
                    await transition_session_status(db, session_id, PipelineStatus.CONVERSION)
                    await asyncio.wait_for(
                        cls._run_speech_conversion(session), timeout=STAGE_TIMEOUT_SECONDS
                    )

                    # Stage 2: Transition to SYNTHESIS (AI Extraction)
                    await transition_session_status(db, session_id, PipelineStatus.SYNTHESIS)
                    await asyncio.wait_for(
                        cls._run_ai_synthesis(session), timeout=STAGE_TIMEOUT_SECONDS
                    )

                    # Stage 3: Transition to COMPLETED
                    await transition_session_status(db, session_id, PipelineStatus.COMPLETED)
                    logger.info(f"Pipeline finished successfully for session {session_id}")

                except asyncio.TimeoutError:
                    logger.error(f"Pipeline stage timed out for session {session_id}")
                    await transition_session_status(
                        db, session_id, PipelineStatus.FAILED, error_message="Processing stage timed out."
                    )
                except asyncio.CancelledError:
                    logger.warning(f"Pipeline execution cancelled for session {session_id}")
                    await transition_session_status(
                        db, session_id, PipelineStatus.FAILED, error_message="Task cancelled by system."
                    )
                except Exception as exc:
                    logger.error(
                        f"Pipeline execution failed for session {session_id}: {str(exc)}",
                        exc_info=True,
                    )
                    await transition_session_status(
                        db, session_id, PipelineStatus.FAILED, error_message=str(exc)
                    )

    @staticmethod
    async def _run_speech_conversion(session: SessionModel) -> None:
        """
        Purpose: Performs Whisper v3 Speech-To-Text conversion on audio file.
        """
        await asyncio.sleep(1.5)  # Simulated asynchronous processing delay

    @staticmethod
    async def _run_ai_synthesis(session: SessionModel) -> None:
        """
        Purpose: Performs AI summary and key action item extraction.
        """
        await asyncio.sleep(1.5)  # Simulated asynchronous LLM processing delay