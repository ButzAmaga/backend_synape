# Session Listing & Cursor Pagination API Specification

## Overview
The Session Listing API exposes a performant, cursor-paginated endpoint for querying active (non-archived) meeting sessions sorted descending by creation date (`created_at DESC`).

To ensure predictable performance on unbounded datasets, offset-based pagination is avoided in favor of **Base64-encoded timestamp cursors**.

---

## Endpoint Definition

- **HTTP Method**: `GET`
- **Path**: `/api/v1/sessions`
- **Authentication**: None (Localhost Environment)
- **Content-Type**: `application/json`

---

## Query Parameters

| Parameter | Type     | Required | Default | Bounds  | Description                                                                 |
| :-------- | :------- | :------- | :------ | :------ | :-------------------------------------------------------------------------- |
| `limit`   | `integer`| No       | `20`    | `1..100`| Maximum number of non-archived session records to return in the current page.|
| `cursor`  | `string` | No       | `null`  | Opaque  | Base64-encoded ISO 8601 timestamp representing the starting pointer cutoff. |

---

## Response Schemas

### `200 OK` — Success Response Body (`CursorPaginatedSessionResponse`)

```json
{
  "items": [
    {
      "id": "c1f7a0b3-e840-410a-8101-92b0c1e84321",
      "title": "Untitled Session",
      "original_file_name": "quarterly_sync.mp3",
      "file_size_bytes": 15482910,
      "mime_type": "audio/mpeg",
      "status": "INGESTION",
      "is_archived": false,
      "category_id": null,
      "created_at": "2026-09-27T21:48:00Z",
      "updated_at": "2026-09-27T21:48:00Z"
    }
  ],
  "next_cursor": "MjAyNi0wOS0yN1QyMTo0ODowMFo=",
  "has_more": true,
  "total": 14
}