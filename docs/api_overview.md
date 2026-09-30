Based on the codebase provided, here are all the defined API endpoints along with their HTTP methods, routes, and purposes:

### 1. Health Checks

* **`GET /api/v1/health`**
* **Purpose:** Evaluates system operational health by pinging the SQLite database to confirm connectivity and checking available host disk space metrics.





---

### 2. Session Operations

* **`POST /api/v1/sessions`**
* **Purpose:** Accepts a multipart audio file upload along with a session title, verifies supported MIME types and available disk space, streams the audio file to disk, creates a session record in the database, and schedules background processing.




* **`GET /api/v1/sessions`**
* **Purpose:** Retrieves a list of active (non-archived) sessions using cursor-based pagination, ordered descending by creation date. Accepts optional `cursor` and `limit` query parameters.




* **`PATCH /api/v1/sessions/{id}`**
* **Purpose:** Updates the title of an existing active session. Fails with `400 Bad Request` if the session is archived.




* **`PATCH /api/v1/sessions/{id}/category`**
* **Purpose:** Assigns or clears a category foreign key link for an active session. Fails with `400 Bad Request` if the session is archived or `404 Not Found` if the specified category does not exist.




* **`POST /api/v1/sessions/{id}/archive`**
* **Purpose:** Archives a session, excluding it from active listing queries and locking it against further modification edits.




* **`DELETE /api/v1/sessions/{id}`**
* **Purpose:** Performs a hard deletion of a session, removing its record from the database and purging its associated audio file from the host disk.