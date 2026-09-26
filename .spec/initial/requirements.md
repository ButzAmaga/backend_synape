# FastAPI Backend Requirements Document (`requirements.md`)

## 1. Introduction
This document defines the backend functional and operational requirements for the **Synapse AI Minutes Studio** FastAPI service. The backend is responsible for local audio file ingestion, local SQLite database management, audio processing pipeline orchestration (Ingestion, Whisper v3 Speech Conversion, and AI Action Extraction), and RESTful API endpoints for the Next.js frontend.

---

## 2. System Requirements (EARS)

### 2.1 Local Storage & File Ingestion
* **[REQ-API-UPL-001] Event-Driven:** WHEN a client posts a valid audio file to the file ingestion endpoint (`POST /api/v1/upload`), THE FASTAPI SERVICE SHALL stream and save the file directly to the local directory (`~/.synapse/audio/`).
* **[REQ-API-UPL-002] Event-Driven:** WHEN a local file write completes successfully, THE FASTAPI SERVICE SHALL create a new database record in the local SQLite database containing the absolute file path, file size, MIME type, and default processing status.
* **[REQ-API-UPL-003] Event-Driven:** WHEN creating a new session record, THE FASTAPI SERVICE SHALL query existing session titles and assign an auto-incremented title formatted as `"Untitled Session"` or `"Untitled Session (N)"` if an entry titled `"Untitled Session"` already exists.
* **[REQ-API-UPL-004] Ubiquitous:** THE FASTAPI SERVICE SHALL isolate incomplete or actively processing audio files in the database state so that they are excluded from completed session listings until pipeline execution finishes successfully.

---

### 2.2 Upload Validation & Input Edge Cases
* **[REQ-API-EDG-001] Event-Driven:** WHEN an uploaded file fails Pydantic MIME type validation (allowing only `.mp3, .wav, .m4a, .aac, .flac`), THE FASTAPI SERVICE SHALL reject the request immediately with an `HTTP 400 Bad Request` and return explicit detail on allowed formats.
* **[REQ-API-EDG-002] Event-Driven:** WHEN an uploaded file exceeds the 500 MB limit, THE FASTAPI SERVICE SHALL reject the request with an `HTTP 413 Payload Too Large` error.
* **[REQ-API-EDG-003] Event-Driven:** WHEN a file stream is interrupted during upload, THE FASTAPI SERVICE SHALL purge any partial file artifacts from the local storage directory (`~/.synapse/audio/`) and return an error status.
* **[REQ-API-EDG-004] Event-Driven:** WHEN an uploaded audio file has a file size of zero bytes or contains no readable audio stream, THE FASTAPI SERVICE SHALL reject the processing request with an `HTTP 400 Bad Request`.
* **[REQ-API-EDG-005] Event-Driven:** WHEN a duplicate audio file is uploaded, THE FASTAPI SERVICE SHALL treat it as an independent payload, store it as a distinct file on local disk, and create a new session entry using the auto-incremented title scheme.

---

### 2.3 Audio Processing Pipeline Execution
* **[REQ-API-PIP-001] Ubiquitous:** THE FASTAPI SERVICE SHALL orchestrate a 3-phase asynchronous workflow lifecycle: Phase 01 Ingestion & Normalization, Phase 02 Whisper v3 Speech Conversion, and Phase 03 AI Synthesis & Action Extraction.
* **[REQ-API-PIP-002] Event-Driven:** WHEN Phase 01 begins, THE FASTAPI SERVICE SHALL update the SQLite session status field to `INGESTION`.
* **[REQ-API-PIP-003] Event-Driven:** WHEN Phase 01 completes, THE FASTAPI SERVICE SHALL update the status field to `CONVERSION` and trigger Phase 02 (Whisper v3 execution).
* **[REQ-API-PIP-004] Event-Driven:** WHEN Phase 02 completes, THE FASTAPI SERVICE SHALL update the status field to `SYNTHESIS` and trigger Phase 03 (AI Action Extraction).
* **[REQ-API-PIP-005] Event-Driven:** WHEN Phase 03 completes, THE FASTAPI SERVICE SHALL mark the session status field as `COMPLETED`.
* **[REQ-API-PIP-006] Event-Driven:** WHEN an unhandled error occurs during any pipeline phase, THE FASTAPI SERVICE SHALL update the session status field to `FAILED` and record the failure stage details in the database log.

---

### 2.4 Session Management & Pagination Endpoints
* **[REQ-API-SES-001] Event-Driven:** WHEN a client requests recent sessions (`GET /api/v1/sessions`), THE FASTAPI SERVICE SHALL return a cursor-paginated JSON response containing active (non-archived) sessions sorted by creation date descending.
* **[REQ-API-SES-002] Event-Driven:** WHEN a client submits a title update request (`PATCH /api/v1/sessions/{id}`), THE FASTAPI SERVICE SHALL validate the payload with Pydantic and update the session title in SQLite.
* **[REQ-API-SES-003] Event-Driven:** WHEN a client submits a category assignment request (`PATCH /api/v1/sessions/{id}/category`), THE FASTAPI SERVICE SHALL update the foreign-key relation in the SQLite database.
* **[REQ-API-SES-004] Event-Driven:** WHEN a client submits an archive request (`POST /api/v1/sessions/{id}/archive`), THE FASTAPI SERVICE SHALL set `is_archived = True` in SQLite, excluding it from recent session queries.
* **[REQ-API-SES-005] State-Driven:** WHILE a session has `is_archived == True`, THE FASTAPI SERVICE SHALL reject any edit or rename mutation attempts with an `HTTP 400 Bad Request`.
* **[REQ-API-SES-006] Event-Driven:** WHEN a client submits a session deletion request (`DELETE /api/v1/sessions/{id}`), THE FASTAPI SERVICE SHALL execute a hard delete, permanently purging the SQLite record and removing the linked audio file from disk (`os.remove`).

---

## 3. Local Database & Security Boundaries
* **[REQ-API-DAT-001] Ubiquitous:** THE FASTAPI SERVICE SHALL maintain a local SQLite database (`~/.synapse/app_data.db`) managed via async SQLAlchemy ORM and Alembic migrations.
* **[REQ-API-DAT-002] Ubiquitous:** THE FASTAPI SERVICE SHALL validate all inbound HTTP query parameters, path parameters, and request bodies using **Pydantic v2** models before reaching the database or file system layer.
* **[REQ-API-DAT-003] Ubiquitous:** THE FASTAPI SERVICE SHALL run on `localhost` (127.0.0.1) and configure CORS headers to restrict API access exclusively to the local Next.js client instance.