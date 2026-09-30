"""
Purpose: Business logic layer for creating, mutating, archiving, and purging session records.
Flow:
      1. Enforce archive guard policy (HTTP 400 when attempting to mutate archived sessions).
      2. Manage session creation, title update, category assignment, archiving, and hard deletion with physical disk file removal.
Inputs: AsyncSession, UploadFile, DTO payloads, session IDs.
Outputs: SessionModel instances, booleans, or raises HTTP exceptions.
"""

import os
import uuid
import pathlib
import aiofiles
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.session import SessionModel, SessionStatus
from app.repositories.session_repository import SessionRepository
from app.repositories.category_repository import CategoryRepository
from app.services.local_storage_service import LocalStorageService

ALLOWED_MIME_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/m4a",
    "audio/x-m4a",
    "audio/mp4",
}


class SessionService:
    """
    Purpose: Service handling session creation lifecycle, mutations, archiving, and physical file deletion.
    """

    def __init__(self, db: AsyncSession):
        self.repository = SessionRepository(db)
        self.category_repository = CategoryRepository(db)

    async def _get_active_session_or_raise(self, session_id: str) -> SessionModel:
        """
        Purpose: Internal helper ensuring session exists and enforcing the archived mutation guard shield.
        Flow:
              1. Fetch session by ID. Raise HTTP 404 if missing.
              2. Check if is_archived is True. Raise HTTP 400 Bad Request if archived.
        Inputs: session_id (str).
        Outputs: Active, non-archived SessionModel instance or raises HTTPException.
        """
        session = await self.repository.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' was not found.",
            )
        if session.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify an archived session. Unarchive the session before making changes.",
            )
        return session

    async def create_session(
        self, title: str, file: UploadFile
    ) -> SessionModel:
        """
        Purpose: Processes uploaded file stream and persists session entity.
        Flow:
              1. Validate file content type.
              2. Inspect disk capacity for required file size.
              3. Stream chunks onto local storage target path.
              4. Commit session record to SQLite database.
        Inputs: title (str), file (UploadFile).
        Outputs: Created SessionModel database object.
        """
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{file.content_type}'. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}",
            )

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        LocalStorageService.verify_disk_space(required_bytes=file_size)

        session_id = str(uuid.uuid4())
        file_extension = pathlib.Path(file.filename or "audio.mp3").suffix
        destination_path = (
            pathlib.Path(settings.AUDIO_STORAGE_DIR) / f"{session_id}{file_extension}"
        )

        try:
            async with aiofiles.open(destination_path, "wb") as out_file:
                while chunk := await file.read(1024 * 1024):
                    await out_file.write(chunk)
        except Exception as err:
            LocalStorageService.cleanup_file(str(destination_path))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to write audio file to local disk.",
            ) from err

        new_session = SessionModel(
            id=session_id,
            title=title,
            file_path=str(destination_path),
            original_file_name=file.filename or "unknown.mp3",
            file_size_bytes=file_size,
            mime_type=file.content_type,
            status=SessionStatus.INGESTION,
        )

        try:
            return await self.repository.create(new_session)
        except Exception:
            LocalStorageService.cleanup_file(str(destination_path))
            raise

    async def update_title(self, session_id: str, new_title: str) -> SessionModel:
        """
        Purpose: Updates title of an active session with mutation shield check.
        Flow:
              1. Validate session exists and is not archived.
              2. Update title via repository.
        Inputs: session_id (str), new_title (str).
        Outputs: Updated SessionModel instance.
        """
        await self._get_active_session_or_raise(session_id)
        updated_session = await self.repository.update_title(session_id, new_title)
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' was not found.",
            )
        return updated_session

    async def assign_category(
        self, session_id: str, category_id: Optional[str]
    ) -> SessionModel:
        """
        Purpose: Assigns or clears category foreign key link on an active session.
        Flow:
              1. Validate session exists and is not archived.
              2. If category_id is provided, verify category exists in database.
              3. Update category foreign key via repository.
        Inputs: session_id (str), category_id (Optional[str]).
        Outputs: Updated SessionModel instance.
        """
        await self._get_active_session_or_raise(session_id)

        if category_id is not None:
            category = await self.category_repository.get_by_id(category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID '{category_id}' was not found.",
                )

        updated_session = await self.repository.update_category(session_id, category_id)
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' was not found.",
            )
        return updated_session

    async def archive_session(self, session_id: str) -> SessionModel:
        """
        Purpose: Archives a session, removing it from active queries and locking mutation edits.
        Flow:
              1. Query session by ID.
              2. Set is_archived = True in database.
        Inputs: session_id (str).
        Outputs: Updated SessionModel instance.
        """
        session = await self.repository.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' was not found.",
            )
        updated_session = await self.repository.set_archived(session_id, True)
        return updated_session  # type: ignore

    async def delete_session(self, session_id: str) -> None:
        """
        Purpose: Executes hard delete of session database record and purges physical local audio file.
        Flow:
              1. Fetch session record from database.
              2. Remove associated local audio file from disk via LocalStorageService.
              3. Hard delete SQLite database row.
        Inputs: session_id (str).
        Outputs: None.
        """
        session = await self.repository.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' was not found.",
            )

        # 1. Purge physical audio file from local disk
        LocalStorageService.cleanup_file(session.file_path)

        # 2. Purge record from SQLite
        await self.repository.delete(session_id)