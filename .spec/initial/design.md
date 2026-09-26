# FastAPI Backend Design & Technical Architecture Specification 

## 1. System & Layered Architecture Overview

Following the **Production API Steering Rules**, the backend is structured as a production-grade, local-first FastAPI service operating on host machine resources (`localhost`). Every inbound client interaction strictly flows through an isolated multi-layered architecture:

```text
Contract (OpenAPI / Pydantic)
  ↓
Authentication & CORS Policy Boundary
  ↓
Validation Layer (Input Bounds, File Header Verification)
  ↓
Authorization & Resource Ownership Checks
  ↓
Use Case / Service Layer (Business Logic & Pipeline Orchestration)
  ↓
Repository Layer (SQLAlchemy Async ORM / Local Storage Manager)
  ↓
Persistence Layer (SQLite DB + Local Disk ~/.synapse/audio/)
  ↓
Response Serialization (Public DTO Schemas)
  ↓
Observability (Structured JSON Logging & Middleware Tracing)

```

---

## 2. Directory & Module Structure

The project strictly segregates HTTP transport mechanics, business logic, repository interactions, and model definitions:

```text
backend/
├── app/
│   ├── api/                           # API Boundary Layer
│   │   ├── middleware/
│   │   │   ├── correlation.py         # Request ID generation & propagation
│   │   │   ├── error_handler.py       # Global exception mapping & sanitization
│   │   │   └── logging.py             # Structured HTTP access logging
│   │   ├── v1/
│   │   │   ├── dependencies.py        # Shared API dependencies (DB session, Rate limiters)
│   │   │   ├── endpoints/
│   │   │   │   ├── health.py          # System readiness & health check endpoint
│   │   │   │   ├── sessions.py        # Session CRUD & Pagination endpoints
│   │   │   │   └── upload.py          # File ingestion endpoint
│   │   │   └── router.py              # Central v1 APIRouter aggregator
│   ├── core/                          # System Configuration & Core Engine
│   │   ├── config.py                  # Pydantic Settings & Environment parsing
│   │   ├── database.py            # SQLite Async Engine & WAL setup
│   │   └── security.py                # Security policies & CORS rules
│   ├── models/                        # Internal DB / Persistence Models
│   │   ├── category.py                # SQLAlchemy Category ORM model
│   │   └── session.py                 # SQLAlchemy Session ORM model
│   ├── repositories/                  # Repository Layer (Data Access)
│   │   ├── category_repository.py     # Category CRUD database queries
│   │   └── session_repository.py      # Session CRUD database queries
│   ├── schemas/                       # Public DTOs (Request / Response Schemas)
│   │   ├── error.py                   # Standard error payload schemas
│   │   ├── health.py                  # System health status schemas
│   │   └── session.py                 # Session Request/Response Pydantic schemas
│   ├── services/                      # Use Case / Business Logic Layer
│   │   ├── audio_processor.py         # Pipeline orchestration (Whisper v3 & AI Action)
│   │   ├── local_storage_service.py   # Atomic file I/O & Disk usage checks
│   │   └── session_service.py         # Session business logic & title deduplication
│   └── main.py                        # FastAPI Application Gateway & Entrypoint
├── alembic/                           # SQLite Database Migration Scenarios
├── requirements.txt                   # Backend Python Dependencies
└── README.md

```

---

## 3. Database Schema & Persistence Design

### 3.1 SQLite Engine Setup (`app/core/database.py`)

To prevent `database is locked` operational errors and permit high-throughput concurrent reads during active background audio processing, the SQLite engine is configured with Write-Ahead Logging (WAL) and an extended busy timeout.

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={
        "timeout": 30,  # 30-second busy timeout for concurrent lock resolution
    },
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

class Base(DeclarativeBase):
    pass

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA synchronous=NORMAL;")

```

### 3.2 SQLAlchemy Domain Models (`app/models/session.py`)

```python
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SessionStatus(str, enum.Enum):
    INGESTION = "INGESTION"
    CONVERSION = "CONVERSION"
    SYNTHESIS = "SYNTHESIS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.INGESTION, nullable=False, index=True
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

```

---

## 4. Contract, Validation & Schema Layer

### 4.1 Standardized Error Payload (`app/schemas/error.py`)

```python
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    code: str = Field(..., example="INVALID_FILE_TYPE")
    message: str = Field(..., example="Unsupported audio format. Allowed: .mp3, .wav, .m4a, .aac, .flac")
    requestId: str = Field(..., example="req_clx982a1b000001")

class ErrorResponse(BaseModel):
    error: ErrorDetail

```

### 4.2 Public DTO Response Models (`app/schemas/session.py`)

Ensures database internal models are never directly exposed to API consumers.

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.models.session import SessionStatus

ALLOWED_MIME_TYPES = ["audio/mpeg", "audio/wav", "audio/x-m4a", "audio/aac", "audio/flac"]

class SessionResponse(BaseModel):
    id: str
    title: str
    original_file_name: str
    file_size_bytes: int
    mime_type: str
    status: SessionStatus
    is_archived: bool
    category_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CursorPaginatedSessionResponse(BaseModel):
    items: list[SessionResponse]
    next_cursor: str | None = None
    has_more: bool

class SessionUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

```

---

## 5. Middleware, Observability & Error Handling

### 5.1 Correlation ID & Request Context Middleware (`app/api/middleware/correlation.py`)

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

```

### 5.2 Global Exception Handler (`app/api/middleware/error_handler.py`)

Sanitizes all unhandled exceptions to prevent stack traces, raw system errors, or secrets from leaking to clients.

```python
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.schemas.error import ErrorResponse, ErrorDetail

logger = logging.getLogger("api.errors")

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled Exception [reqId={request_id}]: {str(exc)}", exc_info=True)
    
    error_payload = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please contact system support.",
            requestId=request_id
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump()
    )

```

---

## 6. Business Logic & Local File Storage Services

### 6.1 Disk Usage & Atomic File I/O (`app/services/local_storage_service.py`)

```python
import os
import shutil
import pathlib
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

class LocalStorageService:
    @staticmethod
    def verify_disk_space(required_bytes: int) -> None:
        usage = shutil.disk_usage(settings.AUDIO_STORAGE_DIR)
        if usage.free < required_bytes:
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail="Insufficient host disk space to complete file upload."
            )

    @staticmethod
    async def save_file_atomically(file: UploadFile, session_id: str) -> pathlib.Path:
        extension = pathlib.Path(file.filename or "").suffix.lower()
        tmp_target = settings.AUDIO_STORAGE_DIR / f"{session_id}.tmp"
        final_target = settings.AUDIO_STORAGE_DIR / f"{session_id}{extension}"

        try:
            with open(tmp_target, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):  # 1 MB Chunk Streaming
                    buffer.write(chunk)
            
            # Atomic File Move
            tmp_target.rename(final_target)
            return final_target
        except Exception as err:
            if tmp_target.exists():
                os.remove(tmp_target)
            raise err

    @staticmethod
    def cleanup_file(file_path_str: str) -> None:
        path = pathlib.Path(file_path_str)
        if path.exists():
            os.remove(path)

```

---

## 7. API Controllers & Routing (HTTP Boundary Layer)

### 7.1 Ingestion Endpoint (`app/api/v1/endpoints/upload.py`)

```python
from fastapi import APIRouter, Depends, UploadFile, File, Header, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_db
from app.schemas.session import SessionResponse
from app.schemas.error import ErrorResponse
from app.services.session_service import SessionService

router = APIRouter()

@router.post(
    "/upload",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        507: {"model": ErrorResponse},
    }
)
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db)
):
    request_id = getattr(request.state, "request_id", "unknown")
    
    # 1. Validation Layer
    if file.size and file.size > 500 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed threshold of 500 MB."
        )
        
    # 2. Service Layer Invocation
    session_service = SessionService(db)
    return await session_service.process_file_upload(
        file=file, 
        idempotency_key=idempotency_key, 
        request_id=request_id
    )

```

---

## 8. Health Check & System Readiness Endpoint

### 8.1 System Health (`app/api/v1/endpoints/health.py`)

```python
import shutil
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.v1.dependencies import get_db
from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
async def check_health(db: AsyncSession = Depends(get_db)):
    # Verify Database Connectivity
    db_healthy = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False

    # Verify Disk Metrics
    disk_usage = shutil.disk_usage(settings.AUDIO_STORAGE_DIR)
    
    return HealthCheckResponse(
        status="HEALTHY" if db_healthy else "UNHEALTHY",
        database_connected=db_healthy,
        disk_free_bytes=disk_usage.free,
        disk_total_bytes=disk_usage.total
    )

```

---

## 9. Steering Rules Compliance Verification

| steering rule requirement | Implementation Design Specification |
| --- | --- |
| **Layered Architecture** | Enforced via explicit directory boundaries (`endpoints/` → `schemas/` → `services/` → `repositories/` → `models/`). |
| **Standard Error Format** | Unified `ErrorResponse` schema with explicit `code`, `message`, and `requestId`. |
| **No Database Exposure** | Explicit Pydantic response models (`SessionResponse`) serialize only public attributes. |
| **Resource Protection & Timeouts** | Background pipelines governed by `asyncio.Semaphore` locks and bounded process timeouts. |
| **Database Lock Prevention** | SQLite connection configured with `PRAGMA journal_mode=WAL;` and 30s busy timeouts. |
| **Idempotency Support** | Header parsing (`Idempotency-Key`) implemented on processing and file creation handlers. |
| **Cursor Pagination** | Bounded limit-and-cursor pagination (`CursorPaginatedSessionResponse`) enforced on all list queries. |
| **Observability & Request Tracing** | Request correlation ID (`X-Request-ID`) middleware attached to every log context and error payload. |

