# Implementation Tasks (`tasks.md`)

## Phase 1: System Core & Health Check (Initial Live Milestone)

### Prerequisites (JIT Setup for Phase 1)
- [x] **TASK-01: Bare-Minimum Foundation & Middleware Setup**
  - **Includes:** Environment configuration (`config.py`), SQLite async engine setup with WAL mode and 30s busy timeout (`database.py`), Correlation ID middleware (`X-Request-ID`), and Global Exception Handler middleware (`error_handler.py`).
  - **Verification:** Run `pytest` or launch FastAPI local server and confirm startup without database lock errors.

### Feature Delivery & Live Verification
- [x] **TASK-02: Health Check Endpoint Implementation**
  - **Endpoint:** `GET /api/v1/health`
  - **Prerequisites:** TASK-01
  - **Includes:** Pydantic schema `HealthCheckResponse` and service check querying SQLite `SELECT 1` and host `shutil.disk_usage()`.
  - **Verification:** Execute `curl http://localhost:8000/api/v1/health` and verify HTTP 200 return containing `{"status": "HEALTHY", "database_connected": true, ...}`.

---

## Phase 2: Audio File Upload & Ingestion

### Prerequisites (JIT Setup for Phase 2)
- [x] **TASK-03: JIT Storage & Session Schema Setup**
  - **Includes:** SQLAlchemy `SessionModel` table definition, initial Alembic migration script, Pydantic `SessionResponse` DTO, and local filesystem directory initialization (`~/.synapse/audio/`).
  - **Verification:** Run Alembic migration to generate `sessions` table in SQLite; verify `~/.synapse/audio/` path creation.

### Feature Delivery & Live Verification
- [x] **TASK-04: Audio File Upload Endpoint**
  - **Endpoint:** `POST /api/v1/upload`
  - **Prerequisites:** TASK-03
  - **Includes:** Payload size validation (500 MB max), disk space check (`shutil.disk_usage`), streaming atomic write (`.tmp` to final path), auto-increment title generator (`"Untitled Session (N)"`), and `Idempotency-Key` header handling.
  - **Verification:** Post a valid `.mp3` file via `curl -F "file=@test.mp3" http://localhost:8000/api/v1/upload`; confirm file is saved atomically to `~/.synapse/audio/` and session record is committed in SQLite.

---

## Phase 3: Session Listing & Cursor Pagination

### Prerequisites (JIT Setup for Phase 3)
- [] **TASK-05: JIT Cursor Pagination Query Helpers**
  - **Includes:** `CursorPaginatedSessionResponse` schema and repository query builder for date-descending cursor pagination filtering non-archived entries.
  - **Verification:** Unit test repository query against SQLite with mock session entries.

### Feature Delivery & Live Verification
- [ ] **TASK-06: Paginated Session Listing Endpoint**
  - **Endpoint:** `GET /api/v1/sessions?limit=10&cursor=...`
  - **Prerequisites:** TASK-04, TASK-05
  - **Includes:** Cursor-based pagination controller enforcing limit parameters.
  - **Verification:** Call `GET http://localhost:8000/api/v1/sessions?limit=1` live; verify response returns the session created in TASK-04 alongside `next_cursor` and `has_more`.

---

## Phase 4: Session Mutations (Update, Category, Archive, Delete)

### Prerequisites (JIT Setup for Phase 4)
- [ ] **TASK-07: JIT Category Schema & Mutation Request DTOs**
  - **Includes:** SQLAlchemy `CategoryModel` table definition, migration script, Pydantic `SessionUpdateRequest`, and category assignment schemas.
  - **Verification:** Run database migration adding `categories` table and foreign key constraint.

### Feature Delivery & Live Verification
- [ ] **TASK-08: Session Title Update Endpoint**
  - **Endpoint:** `PATCH /api/v1/sessions/{id}`
  - **Prerequisites:** TASK-04, TASK-07
  - **Verification:** Send `PATCH` payload with `{"title": "Project Sync"}`; confirm updated title in database.

- [ ] **TASK-09: Category Assignment Endpoint**
  - **Endpoint:** `PATCH /api/v1/sessions/{id}/category`
  - **Prerequisites:** TASK-07, TASK-08
  - **Verification:** Assign a valid category ID to session; verify foreign key link in SQLite.

- [ ] **TASK-10: Session Archive & Mutation Shield Endpoint**
  - **Endpoint:** `POST /api/v1/sessions/{id}/archive`
  - **Prerequisites:** TASK-08
  - **Includes:** Archive state toggle and guard logic blocking edits on archived records with HTTP 400.
  - **Verification:** Call archive endpoint on session; attempt a title update via `PATCH` and confirm API rejects mutation with `HTTP 400 Bad Request`.

- [ ] **TASK-11: Hard Delete Session Endpoint**
  - **Endpoint:** `DELETE /api/v1/sessions/{id}`
  - **Prerequisites:** TASK-04
  - **Includes:** Database record purge and physical disk file cleanup (`os.remove`).
  - **Verification:** Call `DELETE` endpoint live; verify SQLite entry is removed and audio file is erased from `~/.synapse/audio/`.

---

## Phase 5: Pipeline Orchestration & Background Processing

### Prerequisites (JIT Setup for Phase 5)
- [ ] **TASK-12: JIT Async Concurrency & Subprocess Helpers**
  - **Includes:** `asyncio.Semaphore` lock initialization for concurrency control, task cancellation handlers, and pipeline state progression helpers (`INGESTION` $\rightarrow$ `CONVERSION` $\rightarrow$ `SYNTHESIS` $\rightarrow$ `COMPLETED`).
  - **Verification:** Test semaphore locking under concurrent async invocations.

### Feature Delivery & Live Verification
- [ ] **TASK-13: Async Audio Processing Pipeline Service**
  - **Endpoint:** Background trigger integrated with `POST /api/v1/upload` & manual retry `POST /api/v1/sessions/{id}/retry`
  - **Prerequisites:** TASK-04, TASK-12
  - **Includes:** Async pipeline execution (Whisper v3 speech conversion & AI Synthesis), bounded process timeouts, and crash-recovery startup handler (`@app.on_event("startup")`) resetting interrupted tasks to `FAILED`.
  - **Verification:** Submit upload; observe status transitions live from `INGESTION` to `COMPLETED` in SQLite; verify error capturing by simulating a sub-process timeout failure.