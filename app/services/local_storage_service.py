"""
Purpose: Handles file system storage operations and disk capacity verification.
Flow:
1. Verify host disk space availability.
2. Manage local storage path creation and atomic file cleanup.
Inputs: Local directory paths and file size metrics.
Outputs: File system status results or raises storage HTTP exceptions.
"""

import os
import shutil
import pathlib
from fastapi import HTTPException, status
from app.core.config import settings

class LocalStorageService:
    """
    Purpose: Encapsulate disk usage checks and file operations for local audio storage.
    Flow:
    1. Verify available disk space against inbound file requirements.
    2. Provide utility functions for safe disk writes and cleans.
    Inputs: None.
    Outputs: LocalStorageService helper instance.
    """
    
    @staticmethod
    def verify_disk_space(required_bytes: int) -> None:
        """
        Purpose: Ensures host system has sufficient free disk space before receiving files.
        Flow:
              1. Query disk capacity metrics for audio storage directory.
              2. Raise HTTP 507 Insufficient Storage if free bytes are less than required amount.
        Inputs: required_bytes (int).
        Outputs: None.
        """
        usage = shutil.disk_usage(settings.AUDIO_STORAGE_DIR)
        if usage.free < required_bytes:
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail="Insufficient host disk space to complete file upload.",
            )
    
    @staticmethod
    def cleanup_file(file_path_str: str) -> None:
        """
        Purpose: Safely delete audio file from disk if it exists.
        Flow:
              1. Resolve file path.
              2. Remove file if path points to an existing file.
        Inputs: file_path_str (str).
        Outputs: None.
        """
        path = pathlib.Path(file_path_str)
        if path.exists():
            os.remove(path)
    