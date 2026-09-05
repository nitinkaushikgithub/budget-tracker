# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository location

The git repo is `D:\Claude-Training\budget-tracker` (the parent `D:\Claude-Training` is **not** a repo). Remote: `github.com/nitinkaushikgithub/budget-tracker`.

## Commands

This machine's base Anaconda `pip` is broken, so **always call the venv's Python explicitly** — never bare `python` or `pip`.

```powershell
# First-time setup
C:\Users\BunnyPari\anaconda3\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Run (UI + API on http://127.0.0.1:8000, Swagger at /docs)
.venv\Scripts\python.exe app.py

# Run with auto-reload during development
$env:BUDGET_RELOAD = "1"; .venv\Scripts\python.exe app.py
```

Runtime config is via env vars, all optional: `BUDGET_HOST` (default `127.0.0.1`), `BUDGET_PORT` (`8000`), `BUDGET_DB` (`./budget.db`), `BUDGET_RELOAD`, `BUDGET_CORS` (comma-separated origins). See `docs/SETUP.md` §4.

### Tests

There is **no test framework**. The test is a manual PowerShell smoke test in `docs/SETUP.md` §6 that exercises every endpoint and must leave the DB empty. Run it against a live server before and after any API change, and add a line to it when adding an endpoint or validator. Promoting it to `pytest` + `fastapi.testclient` (with a temp `BUDGET_DB` per test) is a pending TODO.

### Reset the database

Stop the server, then delete `budget.db`, `budget.db-wal`, `budget.db-shm`. The schema is recreated empty on next start.

## Architecture

Three source files, no build step:

- **`app.py`** — FastAPI app. Route handlers (`/api/health`, `/api/categories`, `/api/expenses` CRUD), Pydantic request/response models, and it also serves `index.html` at `GET /` (same origin, so the bundled UI needs no CORS). Holds `CATEGORIES` — the **single source of truth** for category id/label/color, served at `/api/categories` and used to validate writes. `lifespan` calls `init_db()` on startup.
- **`db.py`** — the **only** module that imports `sqlite3` or knows the schema. `SCHEMA` (the DDL), `connect()` (Row dicts + WAL + FK pragmas), `get_conn()` (a FastAPI `yield` dependency: one connection per request, commits on clean return, rolls back on exception), `init_db()` (`CREATE ... IF NOT EXISTS` only — **no migrations**).
- **`index.html`** — single-file vanilla-JS UI (HTML + CSS + JS, no framework, no external assets). All network calls go through the `api()` wrapper; the in-memory `expenses` array is kept in sync from write **responses**, not by guessing.

Data flow: browser `fetch()` → `/api/*` handler → Pydantic validation → parameterised SQL via `get_conn` → SQLite `budget.db`. The API is the contract; no client (including the bundled UI) ever reaches the database directly. `docs/ARCHITECTURE.md` has context/component/sequence/ER diagrams.

`CATEGORY` is not a table — it's the `CATEGORIES` list in `app.py`; `expense.category` is validated against it in app code, so there is no DB-level FK.

## Conventions (from docs/BEST_PRACTICES.md)

- **Validation is server-side, always**, via `@field_validator` methods on `ExpenseIn` that raise `ValueError("short message")` → FastAPI returns `422` with that message. Client-side checks are UX only.
- **Status codes:** `201` create, `200` update, `204` (no body) delete, `404` unknown id, `422` bad input. Don't add others without updating `docs/API.md` §1.1.
- **SQL:** always parameterise (`"... WHERE id = ?", (id,)`) — never f-string user input. Any new column used for filtering/sorting needs a matching index in `db.py: SCHEMA`.
- **DB access:** only through the `get_conn` dependency — no ad-hoc `sqlite3.connect`. If you're writing SQL outside `app.py` handlers, add a function to `db.py` instead.
- **Schema changes on a populated DB** need an explicit migration step (DDL + backup + rollback), documented; bump the `version` in `FastAPI(...)` if the response shape changes.
- **Config:** new options are env vars with a safe default, read in one place — not scattered `os.environ` lookups.
- **Timestamps:** stored UTC as `YYYY-MM-DDTHH:MM:SSZ`. The "this month" figure is computed client-side from the local clock.
- **Dependencies:** runtime deps stay `fastapi` + `uvicorn`, pinned to exact versions. A third runtime dep needs a justification note in `docs/REQUIREMENTS.md` (NFR-2).
- **Frontend:** no build step, no CDN scripts, no web fonts — everything in `index.html`, loads offline. Never `innerHTML`/`insertAdjacentHTML` with API or user values; build nodes with the `el()` helper and `textContent`. The sole exception is `donutSVG()` (numbers + `escapeXml()`-ed labels only). Only theme and currency go in `localStorage`; expense data never does. Match the existing `var`/`function` JS style rather than mixing in `const`/arrow syntax.
- **Security:** treat v1.0 as localhost-only; never add a default that binds `0.0.0.0`. Don't commit `budget.db` (it holds personal financial data).
- **Docs travel with code:** a behaviour change updates the relevant `docs/` file and its changelog in the **same commit**, and moves/adds the `docs/TODO.md` item.
