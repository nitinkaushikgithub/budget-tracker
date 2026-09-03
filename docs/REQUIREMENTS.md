# Budget Tracker — Requirements Specification

- **Document status:** Baseline v1.0
- **Last updated:** 2026-09-03
- **Owner:** project maintainer
- **Related docs:** [ARCHITECTURE](ARCHITECTURE.md) · [API](API.md) · [USER_GUIDE](USER_GUIDE.md) · [SETUP](SETUP.md)

---

## 1. Purpose

Provide a lightweight, self-hosted application for recording personal expenses,
classifying each by category, and viewing a visual breakdown of spending. Data is
held in a single relational database and all reads/writes go through a documented
HTTP API so the same backend can later serve other clients (mobile app, CLI,
scripts, a different web front end).

## 2. Scope

### 2.1 In scope (v1.0)

- Single-user, single-machine deployment (run locally, use from a browser).
- Manual entry of expense records.
- Fixed category taxonomy supplied by the server.
- Create / read / update / delete of expense records via REST API.
- Visual summary: totals, per-category breakdown, donut chart.
- Client-side filtering (by category, by description text).
- Currency symbol and light/dark theme as UI preferences.

### 2.2 Out of scope (v1.0 — see [TODO](TODO.md))

- Authentication, authorization, multi-user accounts.
- Cloud sync or multi-device sharing of data.
- Income tracking, budgets/limits, recurring transactions, attachments.
- Server-side reporting/aggregation endpoints, pagination, bulk endpoints.
- Automatic data migration from the earlier browser-only (localStorage) version.

## 3. Stakeholders and users

| Actor | Description | Needs |
|-------|-------------|-------|
| End user | The person tracking their own spending | Fast entry, clear breakdown, edit/delete mistakes, trust that data persists |
| Integrator / developer | Builds another client or script against the API | Stable, documented endpoints; predictable errors; local setup in minutes |
| Maintainer | Keeps the project running | Small dependency surface, readable code, tests, docs |

## 4. Functional requirements

IDs are stable references for traceability. **MoSCoW**: M = Must, S = Should, C = Could.

### 4.1 Expense entry

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-1 | M | The user can create an expense with **amount**, **description**, **category**, and **date**. |
| FR-2 | M | **Amount** must be a number greater than 0; it is stored rounded to 2 decimal places. |
| FR-3 | M | **Description** is required, trimmed of surrounding whitespace, and limited to 120 characters. |
| FR-4 | M | **Category** must be one of the ids returned by the categories endpoint; any other value is rejected. |
| FR-5 | M | **Date** must be a valid calendar date in `YYYY-MM-DD` format. |
| FR-6 | S | The entry form defaults the date to today. |
| FR-7 | S | Invalid input is rejected by the API with a client-error status and a machine-readable reason. |

### 4.2 Category taxonomy

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-8 | M | The server is the single source of truth for the category list. |
| FR-9 | M | Each category has a stable `id`, a human `label`, and a display `color`. |
| FR-10 | M | v1.0 categories: `food`, `groceries`, `transport`, `housing`, `utilities`, `entertainment`, `health`, `shopping`, `education`, `other`. |

### 4.3 Viewing and listing

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-11 | M | The user can list all expense records. |
| FR-12 | M | Records are returned most-recent first (by `date`, then creation time). |
| FR-13 | M | Each row shows date, description, category (with colour marker), and amount. |
| FR-14 | S | The API supports filtering the list by `category`, by `month` (`YYYY-MM`), and by description substring (`q`). |
| FR-15 | S | The UI provides category filter chips and a description search box. |

### 4.4 Editing and deleting

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-16 | M | The user can edit any field of an existing record. |
| FR-17 | M | The user can delete a record; the UI asks for confirmation first. |
| FR-18 | M | Editing or deleting a non-existent record returns a not-found error. |
| FR-19 | M | An update refreshes the record's `updated_at` timestamp. |
| FR-20 | C | The user can delete all records (UI performs this as repeated single deletes). |

### 4.5 Summary and visualisation

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-21 | M | The UI shows total spend, spend for the current calendar month, record count, and the highest-spend category. |
| FR-22 | M | The UI shows a donut chart of spend share by category, with a legend giving each category's colour, amount and percentage of the total. Every category present gets a minimum visible arc so its colour shows even when its share is tiny; the legend always carries the exact percentages. |
| FR-23 | S | When there are no records, the summary shows an explanatory empty state instead of an empty chart. |

### 4.6 Preferences

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-24 | S | The user can choose a currency symbol (₹, $, €, £); it is applied to every displayed amount. |
| FR-25 | S | The user can switch theme between System, Light, and Dark. |
| FR-26 | M | Preferences are per-browser and MUST NOT be stored in the expense database. |

### 4.7 Persistence

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-27 | M | Every create/update/delete is written to the database before the API responds success. |
| FR-28 | M | Data survives closing the browser, restarting the server, and restarting the machine. |
| FR-29 | M | The database schema is created automatically on first run if absent. |

## 5. Non-functional requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Platform | Runs on Windows/macOS/Linux with Python 3.9+ (developed and verified on CPython 3.12). |
| NFR-2 | Dependencies | Runtime third-party packages limited to `fastapi` and `uvicorn`; database uses the Python standard-library `sqlite3`. |
| NFR-3 | Performance | For a personal dataset (≤ ~10 000 rows) list/summary requests complete in < 100 ms on typical hardware. Indexes exist on `date` and `category`. |
| NFR-4 | Data integrity | `amount > 0` enforced by a database `CHECK` constraint in addition to API validation. Writes are transactional (commit on success, rollback on error). |
| NFR-5 | Portability | The database is one file (`budget.db`); backup = copy the file. Location overridable via `BUDGET_DB`. |
| NFR-6 | Configurability | Host, port, DB path, auto-reload, and CORS origins are configurable via environment variables without code changes. |
| NFR-7 | Security posture | v1.0 has **no authentication**; it binds to `127.0.0.1` by default and is intended for local use only. Exposing it on a network requires adding auth and TLS (out of scope). |
| NFR-8 | Input safety | All API input is validated server-side. The front end renders user text via DOM text nodes (no `innerHTML` for user data), avoiding stored XSS. |
| NFR-9 | Browser support | Latest Chrome, Edge, Firefox, Safari. Requires `fetch`, `Promise.prototype.finally`, CSS custom properties. |
| NFR-10 | Accessibility | Colour is never the only signal (labels accompany category colours); form controls have associated `<label>`s; theme respects `prefers-color-scheme`. |
| NFR-11 | Observability | The server logs each request to stdout/stderr (Uvicorn access + app logs). |
| NFR-12 | Maintainability | Backend is three small modules (`app.py`, `db.py`, plus the static `index.html`); no ORM; SQL is inline and readable. |

## 6. Data model

**Entity: `expense`**

| Field | Type | Rules |
|-------|------|-------|
| `id` | string (UUID v4) | Primary key, server-generated |
| `amount` | number | `> 0`, 2 decimal places |
| `description` | string | 1–120 chars, trimmed |
| `category` | string | Must match a known category `id` |
| `date` | string | `YYYY-MM-DD`, valid calendar date |
| `created_at` | string | UTC ISO-8601 `YYYY-MM-DDTHH:MM:SSZ`, set on insert |
| `updated_at` | string | UTC ISO-8601, set on insert and every update |

Indexes: `idx_expenses_date(date)`, `idx_expenses_category(category)`.

**Value object: `category`** — `{ id, label, color }`, defined in code (`app.py: CATEGORIES`), not stored in the database.

## 7. Constraints and assumptions

- **A1** Single writer at a time is assumed; SQLite in WAL mode tolerates concurrent readers but heavy concurrent writes are not a target.
- **A2** The user's machine clock is correct (used for `created_at`/`updated_at` and the "this month" figure).
- **A3** Amounts are stored as `REAL` (floating point). Acceptable for personal tracking; if exact decimal accounting is later required, migrate to integer minor units (see [TODO](TODO.md)).
- **C1** No network exposure without additional security work (NFR-7).
- **C2** Category list changes require a code change and server restart.

## 8. Acceptance criteria (v1.0 exit)

1. Fresh checkout → documented setup → `python app.py` serves the UI at `http://127.0.0.1:8000`.
2. Creating, listing, editing, and deleting an expense through the UI all persist across a server restart.
3. The four listed invalid inputs (amount ≤ 0, unknown category, malformed date, empty description) are rejected with a `4xx` status.
4. `GET /api/expenses` reflects writes made by any client (UI or direct API call).
5. Deleting `budget.db` and restarting recreates an empty, working schema.
6. All endpoints in [API.md](API.md) respond as documented (verified by the smoke test in [SETUP.md](SETUP.md)).

## 9. Traceability

| Requirement | Implemented in | Verified by |
|-------------|----------------|-------------|
| FR-1..FR-7 | `app.py` `ExpenseIn`, `create_expense` | API smoke test; UI form |
| FR-8..FR-10 | `app.py` `CATEGORIES`, `/api/categories` | `GET /api/categories` returns 10 |
| FR-11..FR-15 | `app.py` `list_expenses`; `index.html` `renderTable`, filters | Filter test in SETUP |
| FR-16..FR-20 | `app.py` `update_expense`, `delete_expense`; `index.html` | CRUD smoke test |
| FR-21..FR-23 | `index.html` `renderSummary`, `donutSVG` | Manual UI check |
| FR-24..FR-26 | `index.html` theme/currency + `localStorage` | Manual UI check |
| FR-27..FR-29 | `db.py` `get_conn`, `init_db`; `app.py` lifespan | Restart persistence test |
