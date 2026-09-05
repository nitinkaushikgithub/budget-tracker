# ADR 0001 — Optional free-text note on an expense

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** architect-ada (design); lead-rhys (review gate); product owner (request)
- **Branch:** `demo/expense-note`
- **Related docs:** [ARCHITECTURE](../ARCHITECTURE.md) §4, §7 · [API](../API.md) §2 · [REQUIREMENTS](../REQUIREMENTS.md) §6 · [BEST_PRACTICES](../BEST_PRACTICES.md) §2 · [SETUP](../SETUP.md) §6

---

## Context

The product owner wants an **optional free-text "note"** on an expense:

- A note is optional; expenses created without one must behave exactly as today.
- Max 200 characters, trimmed of surrounding whitespace. An empty string after
  trimming is stored as **no note (`NULL`)**, never `""`.
- The note is returned by every endpoint that returns an expense, and is
  settable on both `POST` (create) and `PUT` (update).
- The UI shows it in the expense list row and makes it editable from the
  add/edit form.

This is an additive field. It touches the storage layer (`db.py: SCHEMA`), the
API contract (`ExpenseIn` / `Expense`, response shape), the SQL in `app.py`, the
front end (`index.html`), and the docs — so it clears the bar for an ADR plus a
work breakdown.

Constraints carried in from `CLAUDE.md` / `BEST_PRACTICES.md`:

- `db.py` stays the only module that knows SQL/schema; `init_db()` stays
  `CREATE ... IF NOT EXISTS` only. A populated DB needs an explicit, documented,
  reversible migration.
- Runtime deps stay `fastapi` + `uvicorn` — this feature adds none.
- Status-code map is fixed (`201/200/204/404/422`).
- Server-side validation via `@field_validator` on `ExpenseIn`.
- Front end builds nodes with `el()` / `textContent` — no `innerHTML` for
  API/user values; only theme + currency live in `localStorage`.
- Localhost-only posture is unaffected.

## Options considered

### 1. How "no note" is stored

| Option | Notes |
|--------|-------|
| **`NULL` (chosen)** | Clean "absent" semantics; matches "optional"; no `""` noise for other API clients / future exports; column stays nullable with no default. |
| Empty string `""` | Would require every consumer to treat `""` and absent the same; contradicts the PO's explicit "not `''`". |

### 2. Over-length input (> 200 chars)

| Option | Notes |
|--------|-------|
| **Silent trim to 200 (chosen)** | Matches the existing `description` convention exactly (`return v[:120]`, `maxlength` in the UI, API.md "truncated to 120"). Keeps the status-code map untouched — no new `422` path. UI `maxlength="200"` makes it unreachable from the bundled client. |
| Reject with `422` | More explicit, but diverges from `description` for no strong reason on a personal-scale tool. If the team prefers this later it is a one-line change in the validator plus flipping one smoke-test assertion. |

### 3. Migrating an existing `budget.db`

| Option | Notes |
|--------|-------|
| **`ALTER TABLE expenses ADD COLUMN note TEXT;` (chosen)** | O(1) in SQLite; existing rows read back `NULL`; nullable, no default. |
| Rebuild table (create-copy-drop-rename) | Unnecessary for a pure add; more moving parts, more risk to personal financial data. |

`init_db()` is **not** changed to run the `ALTER` — it stays
`CREATE ... IF NOT EXISTS`. The migration is a separate, documented manual step
(work-breakdown Task 2).

### 4. Indexing / search

`note` is not filtered or sorted on, so **no index** is added. The `q` query
parameter continues to match **`description` only** — extending it to notes is
out of scope for this change (noted as a possible follow-up in `docs/TODO.md`).

### 5. `PUT` semantics for `note`

`PUT` is already a **full replace** ("all body fields required", API.md §3.5).
`note` follows the same rule: a `PUT` body that **omits** `note` (or sends
`null` / `""`) **clears** any existing note. It does not mean "leave unchanged".
Partial update stays a separate backlog item (`PATCH`, TODO P2). The bundled UI
always sends the field from the form and pre-fills it on edit, so a normal
edit round-trips the note unchanged.

### 6. Where the note shows in the list

| Option | Notes |
|--------|-------|
| **Secondary muted line inside the Description cell (chosen)** | No new column/header; survives the stacked layouts at ~640px and ~380px; keeps the row scannable; built with `el()` + `textContent`. |
| New "Note" table column | Sixth column is heavy at ~380px; most rows would be empty. |
| Tooltip / `title` only | Not visible enough; fails "shows in the expense list row". |

## Decision

Add a nullable `note TEXT` column to `expenses`. Add `note: Optional[str] = None`
to `ExpenseIn` with an `@field_validator` that returns `None` for `None` /
whitespace-only input and otherwise the surrounding-trimmed value capped at 200
characters. `Expense` inherits the field; `SELECT *` already carries it to every
response. Extend the `INSERT` and `UPDATE` statements in `app.py`. Bump the API
version to **1.1.0** (response shape changed). Provide a documented, reversible
one-time migration for populated databases. In the UI, add a labelled 200-char
note input to the add/edit form (sent trimmed, `null` when empty, synced from the
write response) and render an existing note as a muted secondary line under the
description.

## Consequences / trade-offs

- **API contract:** every `Expense` object gains a `note` field (`string` or
  `null`). Version → `1.1.0`; `docs/API.md` §2.1/§2.3 + changelog, plus
  `docs/REQUIREMENTS.md` §6 and `docs/ARCHITECTURE.md` §4, updated in the same
  commits as the code.
- **Client impact:** an integrator issuing `PUT` must include `note` to keep it;
  omitting it wipes the note. This is consistent with existing full-replace `PUT`
  behaviour and is called out explicitly in `docs/API.md`.
- **Populated DBs:** anyone with an existing `budget.db` runs the one-time
  migration (Task 2). Fresh installs and the "delete `budget.db*` and restart"
  reset path are unaffected — the updated `SCHEMA` creates the column.
- **No new runtime dependency.** `fastapi` + `uvicorn` unchanged; NFR-2 holds.
- **Status-code map unchanged.** Trim-don't-reject means no new `422` path;
  a wrong-type `note` (e.g. a number) still yields Pydantic's standard `422`,
  as it does for every field today.
- **Search:** `q` still does not match notes. Minor, logged as a follow-up.
- **UI:** list rows with a note are slightly taller; long notes wrap inside the
  description cell. Both themes and ~380px width are covered by acceptance
  criteria. No `localStorage` change; `donutSVG()` untouched.
- **Localhost-only / security posture:** unaffected.

## Rollback

1. **Code:** revert the `demo/expense-note` branch. Old code with a `note`
   column present is harmless — `response_model=Expense` (without the field)
   simply drops the extra key.
2. **Database (preferred):** restore the pre-migration backup copy
   (`Copy-Item budget.db.bak budget.db` with the server stopped). No existing
   row had a note, so nothing is lost.
3. **Database (alternative):** on SQLite ≥ 3.35
   (`.venv\Scripts\python.exe -c "import sqlite3; print(sqlite3.sqlite_version)"`),
   `ALTER TABLE expenses DROP COLUMN note;`.
4. Re-running `ADD COLUMN` errors with "duplicate column name" — the migration
   procedure checks `PRAGMA table_info(expenses)` first, so it is safe to abort
   and retry.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-09-05 | Created (Proposed). Optional `note` field on expenses. |
| 2026-09-05 | Accepted after lead-rhys review and qa-iris PASS. |
