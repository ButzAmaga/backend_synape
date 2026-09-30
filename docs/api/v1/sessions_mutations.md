Here is the updated technical documentation covering **Phase 4: Session Mutations (TASK-07 through TASK-11)**. You can save this or append it to your project documentation under `docs/api/v1/sessions_mutations.md`.

---

# Phase 4 API Specification: Session Mutations & Lifecycle Operations

## Overview

Phase 4 extends the meeting session API with mutation, categorization, archiving, and purge operations. It includes strict validation for request bodies, foreign key constraints, file cleanup routines, and an **Archive Mutation Shield** that blocks modification of archived sessions with `400 Bad Request`.

---

## Endpoint Summary

| Endpoint | Method | Status Code | Purpose |
| --- | --- | --- | --- |
| `/api/v1/sessions/{id}` | `PATCH` | `200 OK` | Rename/update session title (TASK-08)

 |
| `/api/v1/sessions/{id}/category` | `PATCH` | `200 OK` | Link or clear category foreign key (TASK-09)

 |
| `/api/v1/sessions/{id}/archive` | `POST` | `200 OK` | Archive session and activate mutation shield (TASK-10)

 |
| `/api/v1/sessions/{id}` | `DELETE` | `204 No Content` | Hard delete DB record and purge disk file (TASK-11)

 |

---

## Endpoint Details

### 1. Renaming Session Title

* **HTTP Method**: `PATCH`
* **Path**: `/api/v1/sessions/{id}`
* **Request Body**:
```json
{
  "title": "Project Sync"
}

```


* **Validation Rules**: `title` string length must be between 1 and 255 characters.


* **Response (`200 OK`)**: Standard `SessionResponse` DTO.


* **Error Behavior**:
* Returns `400 Bad Request` if the session is currently archived.


* Returns `404 Not Found` if the session ID does not exist.





---

### 2. Category Assignment

* **HTTP Method**: `PATCH`
* **Path**: `/api/v1/sessions/{id}/category`
* **Request Body**:
```json
{
  "category_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}

```


*(Pass `"category_id": null` to remove category assignment)*
* **Response (`200 OK`)**: Standard `SessionResponse` DTO reflecting updated `category_id`.


* **Error Behavior**:
* Returns `400 Bad Request` if the session is currently archived.


* Returns `404 Not Found` if the target category or session ID does not exist.





---

### 3. Session Archiving & Mutation Shield

* **HTTP Method**: `POST`
* **Path**: `/api/v1/sessions/{id}/archive`
* **Request Body**: None
* **Response (`200 OK`)**: Standard `SessionResponse` DTO with `"is_archived": true`.


* **Mutation Shield Policy**:
* Once archived, the session is hidden from default GET list responses.


* Any subsequent `PATCH` requests (title update or category assignment) targeted at this session ID will be rejected immediately with an HTTP 400 error:


```json
{
  "detail": "Cannot modify an archived session. Unarchive the session before making changes."
}

```





---

### 4. Hard Delete Session

* **HTTP Method**: `DELETE`
* **Path**: `/api/v1/sessions/{id}`
* **Response**: `204 No Content`
* **Side Effects**:
1. Locates the binary audio file recorded in `file_path` and physically deletes it from local disk storage (`~/.synapse/audio/`).


2. Permanently removes the session row entry from the SQLite `sessions` table.




* **Error Behavior**: Returns `404 Not Found` if the session ID does not exist.