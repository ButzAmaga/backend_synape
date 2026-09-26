# TASK-04: Session Ingestion & Upload API Specification

## 1. Overview
TASK-04 implements the primary audio file ingestion endpoint (`POST /api/v1/sessions`). It handles multipart form file uploads, enforces audio MIME type validation, verifies available host disk storage capacity prior to streaming, persists binary payloads onto disk, records metadata in SQLite via `SessionRepository`, and dispatches an asynchronous background task for audio conversion.

---

## 2. API Endpoint Specification

### `POST /api/v1/sessions`
* **Request Content-Type:** `multipart/form-data`
* **Form Fields:**
  * `title` (string, required): Descriptive title for the meeting session.
  * `file` (binary stream, required): Audio recording file (`.mp3`, `.wav`, `.m4a`, `.mp4`).
* **Response Status Codes:**
  * `201 Created`: Upload successful, session created, background pipeline triggered.
  * `400 Bad Request`: File type not permitted or missing required parameters.
  * `507 Insufficient Storage`: Host disk free space is lower than file size.

---

## 3. Storage & Error Cleanup Strategy
* **Chunk Streaming:** Uploads write in 1 MB chunks to prevent RAM exhaustion.
* **Atomic Cleanup:** If database transaction fails after file write, `LocalStorageService.cleanup_file` deletes the orphan audio file.

---

## 4. Operational Flow Architecture

1. Receive multipart form payload -> `create_session()`.
2. Inspect `file.content_type` against `ALLOWED_MIME_TYPES`.
3. Check system free space via `LocalStorageService.verify_disk_space()`.
4. Generate UUID session ID and stream payload to disk location.
5. Create `SessionModel` database record in state `INGESTION`.
6. Attach non-blocking `BackgroundTasks` entry for conversion.
7. Return `SessionResponse` payload with HTTP 201 Created.