"""
Purpose: Exposes session management routes including upload triggers, status queries, pagination, and pipeline retries.
"""

import os
import uuid
import pathlib
import shutil
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.session import SessionModel, SessionStatus
from app.schemas.session import (
    SessionResponse,
    SessionUpdateRequest,
    CategoryAssignmentRequest,
    CursorPaginatedSessionResponse,
)
from app.schemas.pipeline import PipelineStatus
from app.schemas.error import ErrorResponse
from app.repositories.session_repository import SessionRepository
from app.services.pipeline_service import AudioProcessorService

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/m4a",
    "audio/x-m4a",
    "audio/mp4",
    "audio/aac",
    "audio/ogg",
    "audio/webm",
    "audio/flac",
}


@router.get(
    "",
    response_model=CursorPaginatedSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="List active sessions with cursor pagination",
)
async def list_sessions(
    cursor: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CursorPaginatedSessionResponse:
    """
    Purpose: Returns cursor-paginated non-archived sessions.
    """
    repo = SessionRepository(db)
    items, next_cursor, has_more, total = await repo.get_all_paginated(
        cursor=cursor, limit=limit
    )
    return CursorPaginatedSessionResponse(
        items=[SessionResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
        has_more=has_more,
        total=total,
    )


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload audio recording and trigger session ingestion",
)
async def create_session(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Purpose: Validates audio upload format, saves file locally, creates database record, and initializes processing.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'.",
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Check local filesystem capacity
    free_bytes = shutil.disk_usage(settings.BASE_DATA_DIR).free
    if free_bytes < file_size:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient storage space available on backend system.",
        )

    session_id = str(uuid.uuid4())
    file_ext = pathlib.Path(file.filename or "audio.mp3").suffix or ".mp3"
    saved_file_name = f"{session_id}{file_ext}"
    target_path = settings.AUDIO_STORAGE_DIR / saved_file_name

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    session = SessionModel(
        id=session_id,
        title=title,
        file_path=str(target_path),
        original_file_name=file.filename or "recording.mp3",
        file_size_bytes=file_size,
        mime_type=file.content_type or "audio/mpeg",
        status=SessionStatus.INGESTION,
        is_archived=False,
    )

    repo = SessionRepository(db)
    created_session = await repo.create(session)

    return SessionResponse.model_validate(created_session)


@router.patch(
    "/{id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update session title",
)
async def update_session_title(
    id: str,
    payload: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Purpose: Renames session if non-archived and existing.
    """
    repo = SessionRepository(db)
    session = await repo.get_by_id(id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' was not found.",
        )

    if session.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify an archived session.",
        )

    updated = await repo.update_title(id, payload.title)
    return SessionResponse.model_validate(updated)


@router.patch(
    "/{id}/category",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign category to session",
)
async def assign_category(
    id: str,
    payload: CategoryAssignmentRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Purpose: Binds or unbinds category association for a session.
    """
    repo = SessionRepository(db)
    session = await repo.get_by_id(id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' was not found.",
        )

    if session.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign category on an archived session.",
        )

    updated = await repo.update_category(id, payload.category_id)
    return SessionResponse.model_validate(updated)


@router.post(
    "/{id}/archive",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive a session",
)
async def archive_session(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Purpose: Flags a session as archived.
    """
    repo = SessionRepository(db)
    session = await repo.get_by_id(id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' was not found.",
        )

    updated = await repo.set_archived(id, is_archived=True)
    return SessionResponse.model_validate(updated)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard delete a session and remove file from disk",
)
async def delete_session(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Purpose: Permanently deletes session record and purges audio asset file.
    """
    repo = SessionRepository(db)
    session = await repo.get_by_id(id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' was not found.",
        )

    if session.file_path and os.path.exists(session.file_path):
        try:
            os.remove(session.file_path)
        except OSError:
            pass

    await repo.delete(id)


@router.post(
    "/{id}/retry",
    response_model=SessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry background pipeline processing for a failed session",
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def retry_session_processing(
    id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """
    Purpose: Re-initiates background processing for a failed or interrupted session.
    """
    repo = SessionRepository(db)
    session = await repo.get_by_id(id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{id}' was not found.",
        )

    if session.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retry processing on an archived session.",
        )

    if session.status in [
        PipelineStatus.INGESTION.value,
        PipelineStatus.CONVERSION.value,
        PipelineStatus.SYNTHESIS.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session pipeline processing is currently in progress.",
        )

    # Reset status to INGESTION before enqueueing
    session.status = PipelineStatus.INGESTION.value
    session.error_message = None
    await db.commit()
    await db.refresh(session)

    # Enqueue background pipeline task
    background_tasks.add_task(AudioProcessorService.process_session, session.id)

    return SessionResponse.model_validate(session)