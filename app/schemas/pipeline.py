"""
Purpose: Pydantic schemas and status enums for the Phase 5 audio processing pipeline.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    INGESTION = "INGESTION"
    CONVERSION = "CONVERSION"
    SYNTHESIS = "SYNTHESIS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineTaskState(BaseModel):
    session_id: str
    status: PipelineStatus
    transcript: Optional[str] = None
    synthesis_result: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)