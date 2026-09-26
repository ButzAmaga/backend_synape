# Phase 3: Session Listing & Cursor Pagination Specification

## 1. Overview
Phase 3 introduces cursor-based pagination for listing meeting session records in descending chronological order (`created_at DESC`). Cursor pagination ensures consistent O(1) performance across large data sets and prevents missing or duplicate items when sessions are added concurrently.

---

## 2. Technical Requirements

### Query Behavior & Filters
* **Sort Order:** `created_at DESC, id DESC`
* **Filter:** Exclude archived entities (`is_archived == False`).
* **Pagination Method:** Opaque base64-encoded ISO timestamp string derived from the last record on the current page.
* **Limit:** Default 20 items per request, configurable via query parameter.

### Schema Specifications

#### `CursorPaginatedSessionResponse`
* `items` (`List[SessionResponse]`): Array of session data transfer objects.
* `next_cursor` (`Optional[str]`): Opaque cursor pointer for requesting the next page. `null` if no additional pages exist.
* `has_more` (`bool`): Flag indicating if further records are available beyond the returned items.
* `total` (`int`): Count of all non-archived session records matching the query scope.

---

## 3. Data Flow Architecture

1. API receives request -> `GET /api/v1/sessions?cursor={cursor}&limit={limit}`.
2. Endpoint passes arguments to `SessionRepository.get_all_paginated(cursor, limit)`.
3. Repository decodes base64 `cursor` to ISO `datetime` filter `created_at < cursor_dt`.
4. Executes DB count query for total non-archived records.
5. Executes item fetch with `limit + 1` window size.
6. Constructs `next_cursor` from `items[-1].created_at` if extra record detected.
7. Encapsulates payload inside `CursorPaginatedSessionResponse` DTO and returns HTTP 200.