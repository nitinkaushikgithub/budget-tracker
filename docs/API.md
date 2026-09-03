# Budget Tracker — API Reference

- **API version:** 1.0.0
- **Base URL (default):** `http://127.0.0.1:8000`
- **Content type:** `application/json` for all request and response bodies (except `GET /` which returns HTML, and `DELETE` which returns no body).
- **Interactive docs:** `GET /docs` (Swagger UI) · `GET /openapi.json` (machine-readable schema)
- **Auth:** none in v1.0 (see [REQUIREMENTS](REQUIREMENTS.md) NFR-7).

---

## 1. Conventions

### 1.1 Status codes

| Code | Meaning in this API |
|------|---------------------|
| `200 OK` | Successful `GET` or `PUT` |
| `201 Created` | Successful `POST` — body is the created resource |
| `204 No Content` | Successful `DELETE` — **no body** |
| `404 Not Found` | Resource id does not exist |
| `405 Method Not Allowed` | Method not supported on that path (e.g. `DELETE /api/expenses`) |
| `422 Unprocessable Entity` | Request body failed validation |

### 1.2 Error shape

FastAPI returns errors as a JSON object with a `detail` key.

**404 / explicit errors** — `detail` is a string:

```json
{ "detail": "expense not found" }
```

**422 validation errors** — `detail` is an array of field errors:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "amount"],
      "msg": "Value error, amount must be greater than 0",
      "input": -5
    }
  ]
}
```

Integrators should treat any `2xx` as success, `422` as "fix the payload", `404`
as "unknown id", and anything else as a transport/server problem.

### 1.3 Timestamps

`created_at` and `updated_at` are UTC, formatted `YYYY-MM-DDTHH:MM:SSZ`
(second precision).

### 1.4 Ordering & pagination

`GET /api/expenses` returns **all** matching rows, ordered by `date` descending
then `created_at` descending. There is no pagination in v1.0.

---

## 2. Data types

### 2.1 `Expense`

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | UUID v4, server-generated |
| `amount` | number | `> 0`, 2 decimal places |
| `description` | string | 1–120 chars, trimmed server-side |
| `category` | string | One of the [`Category.id`](#22-category) values |
| `date` | string | `YYYY-MM-DD` |
| `created_at` | string | UTC ISO-8601, set on create |
| `updated_at` | string | UTC ISO-8601, updated on every write |

### 2.2 `Category`

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Stable key used in `Expense.category` |
| `label` | string | Human-readable name |
| `color` | string | Hex colour for charts/markers |

v1.0 ids: `food`, `groceries`, `transport`, `housing`, `utilities`,
`entertainment`, `health`, `shopping`, `education`, `other`.

### 2.3 `ExpenseInput` (request body for POST and PUT)

```json
{
  "amount": 249.5,
  "description": "Weekly groceries",
  "category": "groceries",
  "date": "2026-09-01"
}
```

Validation rules (server-side, all fields required):

| Field | Rule | Message on failure |
|-------|------|--------------------|
| `amount` | number, `> 0` | `amount must be greater than 0` |
| `description` | non-empty after trim; truncated to 120 | `description is required` |
| `category` | in the known id set | `unknown category: '<value>'` |
| `date` | parses as `YYYY-MM-DD` calendar date | `date must be 'YYYY-MM-DD'` |

---

## 3. Endpoints

### 3.1 `GET /api/health`

Liveness probe.

**Response `200`**

```json
{ "status": "ok" }
```

---

### 3.2 `GET /api/categories`

Returns the full category taxonomy. Use this to build a category picker and to
map `category` ids to labels/colours.

**Response `200`**

```json
[
  { "id": "food",      "label": "Food & Dining",  "color": "#4e79a7" },
  { "id": "groceries", "label": "Groceries",      "color": "#59a14f" }
]
```

---

### 3.3 `GET /api/expenses`

List expense records, newest first.

**Query parameters** (all optional, combinable):

| Param | Type | Effect |
|-------|------|--------|
| `category` | string | Only rows with this exact category id |
| `month` | string `YYYY-MM` | Only rows whose `date` falls in that calendar month |
| `q` | string | Case-insensitive substring match on `description` |

**Response `200`** — array of [`Expense`](#21-expense):

```json
[
  {
    "id": "add0b3a9-aa73-4c4e-a583-ca0cd8933ca9",
    "amount": 249.5,
    "description": "Weekly groceries",
    "category": "groceries",
    "date": "2026-09-01",
    "created_at": "2026-09-03T09:07:16Z",
    "updated_at": "2026-09-03T09:07:16Z"
  }
]
```

**Examples**

```bash
curl "http://127.0.0.1:8000/api/expenses"
curl "http://127.0.0.1:8000/api/expenses?month=2026-09"
curl "http://127.0.0.1:8000/api/expenses?category=transport&q=metro"
```

---

### 3.4 `POST /api/expenses`

Create a record. The server generates `id`, `created_at`, `updated_at`.

**Request body** — [`ExpenseInput`](#23-expenseinput-request-body-for-post-and-put)

**Response `201`** — the created [`Expense`](#21-expense).

**Response `422`** — validation failed (see [1.2](#12-error-shape)).

**Example**

```bash
curl -X POST "http://127.0.0.1:8000/api/expenses" \
  -H "Content-Type: application/json" \
  -d '{"amount": 60, "description": "Metro card", "category": "transport", "date": "2026-09-02"}'
```

---

### 3.5 `PUT /api/expenses/{id}`

Full update of an existing record. All body fields are required (there is no
`PATCH`). `id`, `created_at` are preserved; `updated_at` is refreshed.

**Path parameter:** `id` — the expense id.

**Request body** — [`ExpenseInput`](#23-expenseinput-request-body-for-post-and-put)

**Response `200`** — the updated [`Expense`](#21-expense).

**Response `404`** — `{ "detail": "expense not found" }`.

**Response `422`** — validation failed.

**Example**

```bash
curl -X PUT "http://127.0.0.1:8000/api/expenses/add0b3a9-aa73-4c4e-a583-ca0cd8933ca9" \
  -H "Content-Type: application/json" \
  -d '{"amount": 300.75, "description": "Weekly groceries (corrected)", "category": "food", "date": "2026-09-01"}'
```

---

### 3.6 `DELETE /api/expenses/{id}`

Delete a record.

**Path parameter:** `id` — the expense id.

**Response `204`** — no body.

**Response `404`** — `{ "detail": "expense not found" }`.

**Example**

```bash
curl -i -X DELETE "http://127.0.0.1:8000/api/expenses/add0b3a9-aa73-4c4e-a583-ca0cd8933ca9"
```

> There is no bulk-delete endpoint. The web UI's "Delete all" issues one
> `DELETE` per row.

---

### 3.7 `GET /`

Serves `index.html` (the web UI). `Content-Type: text/html`.

---

## 4. Integration notes

- **CORS.** Disabled by default (the API serves its own front end, same origin).
  To call from another origin, start the server with
  `BUDGET_CORS="http://localhost:5173,https://myapp.example"`. Allowed methods:
  `GET, POST, PUT, DELETE, OPTIONS`; allowed header: `Content-Type`.
- **Base URL.** Configurable via `BUDGET_HOST` / `BUDGET_PORT` (see [SETUP](SETUP.md)).
- **Idempotency.** `PUT` and `DELETE` are idempotent; `POST` is not (each call creates a new row with a new `id`).
- **Concurrency.** Last write wins. There is no optimistic-locking / `If-Match` support; `updated_at` is informational.
- **Client-side mapping.** Fetch `/api/categories` once at startup and cache it; join on `category` id for labels and colours.
- **Schema source of truth.** `GET /openapi.json` always matches the running server; generate typed clients from it if needed.

## 5. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-09-03 | Initial API: health, categories, expenses CRUD, list filters. |
