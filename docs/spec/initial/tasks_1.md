Here is a simple, straightforward breakdown of every file and piece of code created in **TASK-01**.

---

### 1. `app/core/config.py` (App Settings)

* **Purpose:** Acts as the central setup manager for the app. It decides where to save database files and audio recordings, and reads environment settings.
* **Code Breakdown:**
* `BASE_DATA_DIR` & `AUDIO_STORAGE_DIR`: Tells the application where to store local data inside your project folder (`.data/` and `.data/audio/`).
* `DATABASE_URL`: Builds the address for your local SQLite database file (`sqlite+aiosqlite:///.data/app_data.db`).
* `setup_directories()`: Automatically creates the `.data/` and `.data/audio/` folders on your hard drive as soon as the app starts so files have a place to live.



---

### 2. `app/core/database.py` (Database Connection)

* **Purpose:** Handles the connection to your local SQLite database and prepares it to handle multiple actions at once without freezing.
* **Code Breakdown:**
* `create_async_engine(...)`: Creates the engine that communicates with SQLite asynchronously (in the background) with a 30-second timeout so it waits patiently if another process is writing data.
* `async_session_factory`: A factory tool used to open and close temporary communication channels (sessions) to read or write database data.
* `init_db()`: Runs on startup and turns on **WAL mode** (`PRAGMA journal_mode=WAL;`). WAL mode allows the app to read from the database and write to it simultaneously without throwing `database is locked` errors.
* `get_db()`: A reusable helper that gives endpoints a clean database connection when an HTTP request arrives and closes it when the request finishes.



---

### 3. `app/schemas/error.py` (Error Message Format)

* **Purpose:** Ensures that whenever an error happens, the API returns a neat, predictable JSON message instead of messy code or raw crash logs.
* **Code Breakdown:**
* `ErrorDetail`: Defines the 3 pieces of information every error message must have: an error `code` (e.g., `INTERNAL_SERVER_ERROR`), a human-readable `message`, and a unique `requestId`.
* `ErrorResponse`: Wraps the error details inside a standard `{ "error": { ... } }` JSON structure for the frontend to easily read.



---

### 4. `app/api/middleware/correlation.py` (Request Tracking)

* **Purpose:** Gives every single incoming HTTP request a unique tracking ID tag (`X-Request-ID`).
* **Code Breakdown:**
* `CorrelationIdMiddleware`: Intercepts every request coming into the server. If the request doesn't have an ID, it generates a unique string (like `req_a1b2c3d4e5f6`) and attaches it to both the request and the response headers. This makes it easy to trace logs for a specific request when debugging.



---

### 5. `app/api/middleware/error_handler.py` (Crash Protection)

* **Purpose:** Acts as a safety net that catches unexpected errors or bugs anywhere in the application so the server doesn't crash or leak sensitive system info.
* **Code Breakdown:**
* `global_exception_handler()`: Catches any unhandled error, logs the full crash detail internally for you (the developer) along with the `requestId`, and sends back a clean, safe `500 Internal Server Error` message to the user without exposing stack traces.



---

### 6. `app/main.py` (App Gateway & Entrypoint)

* **Purpose:** The main entry point where the entire FastAPI application is assembled and launched.
* **Code Breakdown:**
* `lifespan(app)`: A startup/shutdown manager that automatically triggers `init_db()` to set up SQLite database tables and WAL mode right as Uvicorn starts up.
* `app = FastAPI(...)`: Creates the web app instance.
* `CORSMiddleware`: Sets security permissions so your local Next.js frontend (`http://localhost:3000`) is allowed to communicate with this FastAPI backend (`http://localhost:8000`).
* `add_middleware(CorrelationIdMiddleware)` & `add_exception_handler(...)`: Attaches the correlation ID tracking and safety net error handling to the entire application.