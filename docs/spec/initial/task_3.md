# TASK-03 Documentation & System Overview

## Simple Explanation of Files & Code Created in Task 3

### 1. `app/models/session.py` (Database Table Structure)

* **Purpose:** Defines the blueprint for the `sessions` table stored inside your local SQLite database.
* **Code Breakdown:**
* `SessionStatus`: An enum (a list of allowed words) tracking where a meeting session is in its lifecycle (`INGESTION` -> `CONVERSION` -> `SYNTHESIS` -> `COMPLETED` or `FAILED`).
* `SessionModel`: The database map. It tells SQLite to store session IDs, meeting titles, file paths, file sizes, MIME types, archive flags, and timestamps.



---

### 2. `app/schemas/session.py` (Data Protection Boundary)

* **Purpose:** Acts as a safe response blueprint that controls what session data is shared with the frontend.
* **Code Breakdown:**
* `SessionResponse`: A Pydantic model that copies session data from the database and converts it into clean JSON. It hides internal database details while sending only public fields (like title, size, status, and creation date) to the client.



---

### 3. `app/repositories/session_repository.py` (Database Operations Manager)

* **Purpose:** Isolates all raw SQL database queries into one place so the rest of the application doesn't need to write SQL queries directly.
* **Code Breakdown:**
* `SessionRepository`: Contains helper functions to query SQLite.
* `create(...)`: Inserts a new session record into the `sessions` table.
* `get_by_id(...)`: Finds a single meeting session using its unique ID.
* `get_all(...)`: Fetches a list of recent sessions sorted from newest to oldest.



---

### 4. `app/services/local_storage_service.py` (Disk Space Guard)

* **Purpose:** Manages the hard drive space inside your `.data/audio/` directory.
* **Code Breakdown:**
* `verify_disk_space(...)`: Checks if your computer has enough free hard drive space before accepting a new file. If disk space is full, it stops the request immediately with an HTTP 507 "Insufficient Storage" error.
* `cleanup_file(...)`: Safely deletes files from the `.data/audio/` directory when needed.



---

## Simple Summary of Tasks 1 and 2

### TASK-01 Summary: Core Server Setup & Protection

* **`app/core/config.py`**: Tells the app where to save database and audio files locally inside your project's `.data/` directory.
* **`app/core/database.py`**: Connects the app to SQLite using asynchronous connections and turns on **WAL mode** so multiple operations can happen simultaneously without locking the database.
* **`app/schemas/error.py`**: Standardizes error formatting so every error returns a clean, predictable `{ "error": { "code": ..., "message": ..., "requestId": ... } }` JSON structure.
* **`app/api/middleware/correlation.py`**: Generates a unique tracking ID (`X-Request-ID`) for every incoming web request.
* **`app/api/middleware/error_handler.py`**: Acts as a safety net that catches unexpected code crashes, logs them safely, and returns a sanitized HTTP 500 message.
* **`app/main.py`**: The entry point that boots up FastAPI, sets security rules (CORS), applies middleware, and initializes SQLite on startup.

### TASK-02 Summary: Health Check Endpoint

* **`app/schemas/health.py`**: Defines the JSON format returned by the health status endpoint.
* **`app/api/v1/endpoints/health.py`**: Listens for requests on `/health`, checks if SQLite is responding using `SELECT 1`, and measures free hard drive space.
* **`app/api/v1/router.py`**: A central directory switchboard that gathers all `/api/v1` routes and exposes them to `app/main.py`.

```

---

### Verification for TASK-03
Restart Uvicorn:
```powershell
uvicorn app.main:app --reload

```

Upon startup, `init_db()` will execute and automatically create the new `sessions` database table in `.data/app_data.db`. You are now completely ready to move on to **TASK-04: Audio File Upload Endpoint**!