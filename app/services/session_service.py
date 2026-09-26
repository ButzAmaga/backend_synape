"""
Purpose: Business logic layer for creating and initializing session records.
Flow:
      1. Verify host storage capacity against inbound file size.
      2. Stream upload binary chunks safely onto persistent disk.
      3. Save initial database record using SessionRepository.
Inputs: UploadFile payload, title string, and active AsyncSession.
Outputs: Created SessionModel instance or raises HTTP error exceptions.
"""

import os
import uuid
import pathlib
import aiofiles
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.session import SessionModel, SessionStatus
from app.repositories.session_repository import SessionRepository
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
    Purpose: Service handling session creation lifecycle and audio file storage.
    Flow:
          1. Validate audio MIME type.
          2. Check available storage space.
          3. Save audio file locally and record database entry.
    Inputs: Database AsyncSession.
    Outputs: SessionService instance.
    """

    def __init__(self, db: AsyncSession):
        self.repository = SessionRepository(db)

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
                while chunk := await file.read(1024 * 1024):  # 1MB Chunks
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