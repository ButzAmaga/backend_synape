# Comprehensive FastAPI Backend Requirements Document (`requirements.md`)

## 1. System Overview & Architecture Rules

### 1.1 Overview
This document defines the comprehensive functional, operational, structural, and edge-case requirements for the **Synapse AI Minutes Studio** FastAPI backend service. The service operates locally on the host machine, using **SQLite** for metadata storage, local filesystem directories for audio storage (`~/.synapse/audio/`), and an asynchronous pipeline for audio processing (Whisper v3 and AI Synthesis).

### 1.2 Core Execution & Architectural Flow
* **[REQ-API-ARC-001] Ubiquitous:** THE FASTAPI SERVICE SHALL process every request through a layered execution pipeline enforcing strict boundary separation: `Contract → Authentication → Validation → Authorization → Use Case / Business Logic → Persistence / External Services → Response → Observability`.
* **[REQ-API-ARC-002] Ubiquitous:** THE FASTAPI SERVICE SHALL maintain a strict layered directory architecture separating HTTP handlers/controllers, request schema validation, authorization, use cases/services, repository persistence, and external model integrations.
* **[REQ-API-ARC-003] Ubiquitous:** THE FASTAPI SERVICE SHALL explicitly map response schemas via Pydantic models to restrict database document models from direct client exposure, returning only explicitly defined public fields.

---

## 2. API Contract & Standardization Requirements

### 2.1 Endpoint Specification & Versioning
* **[REQ-API-CTR-001] Ubiquitous:** THE FASTAPI SERVICE SHALL explicitly define HTTP method, path `/api/v1/...`, authentication, authorization, request parameters, request body, response schema, error schema, and status codes for every endpoint.
* **[REQ-API-CTR-002] State-Driven:** WHILE applying API updates or schema changes, THE FASTAPI SERVICE SHALL maintain backward compatibility by enforcing an "add before removing" additive change strategy.

### 2.2 Standard Error Response Structure
* **[REQ-API-ERR-001] Ubiquitous:** THE FASTAPI SERVICE SHALL return a standardized, predictable error payload structure across all endpoints formatted as follows:
  ```json
  {
    "error": {
      "code": "STRING_ERROR_CODE",
      "message": "Human-readable error description.",
      "requestId": "req_unique_identifier"
    }
  }

```

* **[REQ-API-ERR-002] Ubiquitous:** THE FASTAPI SERVICE SHALL sanitize all error responses to strictly forbid exposing stack traces, filesystem secrets, internal configuration paths, or database implementation details to the client.

### 2.3 HTTP Semantics

* **[REQ-API-SEM-001] Ubiquitous:** THE FASTAPI SERVICE SHALL emit precise HTTP status codes mapped to exact execution outcomes, including `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `413 Payload Too Large`, `422 Unprocessable Content`, `429 Too Many Requests`, `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable`, and `507 Insufficient Storage`.

---

## 3. Audio Ingestion & Local File System Requirements

### 3.1 File Ingestion & Storage

* **[REQ-API-UPL-001] Event-Driven:** WHEN a client posts an audio file payload to the upload endpoint (`POST /api/v1/upload`), THE FASTAPI SERVICE SHALL stream the incoming file directly to the local storage directory (`~/.synapse/audio/`).
* **[REQ-API-UPL-002] Event-Driven:** WHEN a local file write completes successfully, THE FASTAPI SERVICE SHALL create a corresponding session record in the local SQLite database capturing the file path, file size, MIME type, and default `INGESTION` status.
* **[REQ-API-UPL-003] Event-Driven:** WHEN creating a new session record, THE FASTAPI SERVICE SHALL query existing session titles and assign an auto-incremented title formatted as `"Untitled Session"` or `"Untitled Session (N)"` if `"Untitled Session"` already exists.
* **[REQ-API-UPL-004] Ubiquitous:** THE FASTAPI SERVICE SHALL isolate actively processing or incomplete audio session records so that they are excluded from completed session views until execution finishes successfully.

### 3.2 File System Edge Cases & Write Safety

* **[REQ-API-EDG-006] Event-Driven:** WHEN a file upload stream is initiated, THE FASTAPI SERVICE SHALL verify available local disk space via `shutil.disk_usage()` against the incoming file size before accepting the upload stream.
* **[REQ-API-EDG-007] State-Driven:** WHILE writing an incoming audio file stream, THE FASTAPI SERVICE SHALL write data into a temporary file extension (`{session_id}.tmp`) inside `~/.synapse/audio/`.
* **[REQ-API-EDG-008] Event-Driven:** WHEN a file upload stream encounters a disk space failure or write exception, THE FASTAPI SERVICE SHALL catch the exception, delete the temporary `.tmp` file, roll back the database transaction, and return an `HTTP 507 Insufficient Storage` error response.
* **[REQ-API-EDG-009] Event-Driven:** WHEN a file upload stream completes with 100% data written, THE FASTAPI SERVICE SHALL atomically rename the file from `{session_id}.tmp` to `{session_id}{extension}` and commit the session database record.
* **[REQ-API-EDG-010] Ubiquitous:** THE FASTAPI SERVICE SHALL ignore client-provided raw filenames for disk storage operations and store all local audio files strictly using their system-generated unique ID (`{session_id}{extension}`).
* **[REQ-API-EDG-011] Event-Driven:** WHEN storing original file metadata in SQLite, THE FASTAPI SERVICE SHALL sanitize client-provided filenames using string stripping and slugification to prevent path traversal vulnerabilities or OS filesystem errors.
* **[REQ-API-EDG-012] Event-Driven:** WHEN an upload HTTP request is cancelled or disconnected mid-stream by the client, THE FASTAPI SERVICE SHALL catch `asyncio.CancelledError` and immediately execute cleanup logic to remove any uncommitted `.tmp` files from disk.

---

## 4. Input Validation & Security Boundaries

* **[REQ-API-VAL-001] Event-Driven:** WHEN an uploaded file fails Pydantic MIME type validation (allowing only `.mp3, .wav, .m4a, .aac, .flac`), THE FASTAPI SERVICE SHALL reject the request immediately with an `HTTP 400 Bad Request` and return explicit detail on supported formats.
* **[REQ-API-VAL-002] Event-Driven:** WHEN an uploaded file exceeds the 500 MB limit, THE FASTAPI SERVICE SHALL reject the request with an `HTTP 413 Payload Too Large` error.
* **[REQ-API-VAL-003] Event-Driven:** WHEN an uploaded audio file has a file size of zero bytes or contains no readable audio stream, THE FASTAPI SERVICE SHALL reject the processing request with an `HTTP 400 Bad Request`.
* **[REQ-API-VAL-004] Event-Driven:** WHEN a duplicate audio file is uploaded, THE FASTAPI SERVICE SHALL treat it as an independent payload, store it as a distinct file on local disk, and create a new session entry using the auto-incremented title scheme.
* **[REQ-API-SEC-001] Ubiquitous:** THE FASTAPI SERVICE SHALL treat all inbound HTTP client input as untrusted, validating types, string lengths, numeric ranges, enumerations, dates, query parameters, path parameters, and payload boundaries at the API schema layer prior to business logic execution.
* **[REQ-API-SEC-002] Ubiquitous:** THE FASTAPI SERVICE SHALL enforce the principle of least privilege for configuration settings, storing secrets and variable configurations exclusively in environment variables or configuration files (`config.py`) and never hard-coding credentials in source code.

---

## 5. Audio Processing Pipeline & Resource Protection

* **[REQ-API-PIP-001] Ubiquitous:** THE FASTAPI SERVICE SHALL orchestrate a 3-phase asynchronous workflow lifecycle: Phase 01 Ingestion & Normalization, Phase 02 Whisper v3 Speech Conversion, and Phase 03 AI Synthesis & Action Extraction.
* **[REQ-API-PIP-002] Event-Driven:** WHEN Phase 01 begins, THE FASTAPI SERVICE SHALL update the SQLite session status field to `INGESTION`.
* **[REQ-API-PIP-003] Event-Driven:** WHEN Phase 01 completes, THE FASTAPI SERVICE SHALL update the status field to `CONVERSION` and trigger Phase 02 (Whisper v3 execution).
* **[REQ-API-PIP-004] Event-Driven:** WHEN Phase 02 completes, THE FASTAPI SERVICE SHALL update the status field to `SYNTHESIS` and trigger Phase 03 (AI Action Extraction).
* **[REQ-API-PIP-005] Event-Driven:** WHEN Phase 03 completes, THE FASTAPI SERVICE SHALL mark the session status field as `COMPLETED`.
* **[REQ-API-PIP-006] Event-Driven:** WHEN an unhandled error occurs during any pipeline phase, THE FASTAPI SERVICE SHALL update the session status field to `FAILED` and record failure stage details in the database log.
* **[REQ-API-RES-001] Ubiquitous:** THE FASTAPI SERVICE SHALL protect heavy audio processing tasks (Whisper v3 inference and AI Action Extraction) using strict concurrency locks (`asyncio.Semaphore`) and request rate limiting to prevent host machine CPU/RAM exhaustion.
* **[REQ-API-RES-002] Ubiquitous:** THE FASTAPI SERVICE SHALL configure explicit bounded timeouts on all internal sub-processes and external inference model API calls to prevent long-running tasks from hanging indefinitely.
* **[REQ-API-RES-003] Event-Driven:** WHEN processing operations with side effects are triggered, THE FASTAPI SERVICE SHALL require and evaluate an `Idempotency-Key` header to prevent duplicate execution on retries.

---

## 6. Session Management & Cursor Pagination

* **[REQ-API-SES-001] Event-Driven:** WHEN a client requests recent sessions (`GET /api/v1/sessions`), THE FASTAPI SERVICE SHALL require limit parameters and return a cursor-paginated JSON response containing active (non-archived) sessions sorted by creation date descending.
* **[REQ-API-SES-002] Event-Driven:** WHEN a client submits a title update request (`PATCH /api/v1/sessions/{id}`), THE FASTAPI SERVICE SHALL validate the payload with Pydantic and update the session title in SQLite.
* **[REQ-API-SES-003] Event-Driven:** WHEN a client submits a category assignment request (`PATCH /api/v1/sessions/{id}/category`), THE FASTAPI SERVICE SHALL update the foreign-key relation in the SQLite database.
* **[REQ-API-SES-004] Event-Driven:** WHEN a client submits an archive request (`POST /api/v1/sessions/{id}/archive`), THE FASTAPI SERVICE SHALL set `is_archived = True` in SQLite, excluding it from recent session queries.
* **[REQ-API-SES-005] State-Driven:** WHILE a session has `is_archived == True`, THE FASTAPI SERVICE SHALL reject any edit or rename mutation attempts with an `HTTP 400 Bad Request`.
* **[REQ-API-SES-006] Event-Driven:** WHEN a client submits a session deletion request (`DELETE /api/v1/sessions/{id}`), THE FASTAPI SERVICE SHALL execute a hard delete, permanently purging the SQLite database record and deleting the associated local audio file from disk (`os.remove`).

---

## 7. Database (SQLite) & Concurrency Edge Cases

* **[REQ-API-DAT-001] Ubiquitous:** THE FASTAPI SERVICE SHALL maintain a local SQLite database (`~/.synapse/app_data.db`) managed via async SQLAlchemy ORM and Alembic migrations.
* **[REQ-API-DAT-002] Ubiquitous:** THE FASTAPI SERVICE SHALL validate all inbound HTTP query parameters, path parameters, and request bodies using **Pydantic v2** models before reaching the database or file system layer.
* **[REQ-API-DAT-003] Ubiquitous:** THE FASTAPI SERVICE SHALL run on `localhost` (127.0.0.1) and configure CORS headers to restrict API access exclusively to the local Next.js client instance.
* **[REQ-API-DAT-004] Ubiquitous:** THE FASTAPI SERVICE SHALL configure the SQLite database connection using Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) to permit concurrent read operations alongside active pipeline write operations.
* **[REQ-API-DAT-005] Ubiquitous:** THE FASTAPI SERVICE SHALL initialize the SQLAlchemy `aiosqlite` async engine with a minimum busy timeout of 30 seconds (`connect_args={"timeout": 30}`) to prevent `database is locked` operational errors during concurrent writes.
* **[REQ-API-DAT-006] Event-Driven:** WHEN evaluating auto-increment title sequence numbers (`"Untitled Session (N)"`), THE FASTAPI SERVICE SHALL execute title checking and increment assignment inside an isolated database transaction block to prevent race conditions during simultaneous uploads.
* **[REQ-API-DAT-007] Event-Driven:** WHEN a database transaction fails during auto-increment assignment, THE FASTAPI SERVICE SHALL catch the collision error, apply a unique fallback identifier, and retry the commit.

---

## 8. Observability, Logging & Readiness Checklist

* **[REQ-API-OBS-001] Ubiquitous:** THE FASTAPI SERVICE SHALL emit structured JSON logs for all request execution flows including a unique correlation ID (`requestId`), endpoint path, execution duration, and caller details.
* **[REQ-API-OBS-002] Ubiquitous:** THE FASTAPI SERVICE SHALL strictly exclude passwords, tokens, API keys, or sensitive unencrypted payloads from log outputs.
* **[REQ-API-OBS-003] Ubiquitous:** THE FASTAPI SERVICE SHALL expose a dedicated `/health` endpoint returning system readiness, database connectivity, and local disk space metrics.
* **[REQ-API-OBS-004] State-Driven:** BEFORE considering any endpoint production-ready, THE FASTAPI SERVICE SHALL fulfill the following readiness criteria:
* [x] Defined OpenAPI contract schema
* [x] Input validation layer enforced
* [x] Standardized error formatting with unique `requestId`
* [x] Bound timeouts on pipeline dependencies
* [x] Concurrency throttling and rate limits
* [x] Cursor pagination on unbounded list queries
* [x] Structured logging and health checks



