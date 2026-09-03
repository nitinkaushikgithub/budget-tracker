# Budget Tracker — Best Practices & Contributor Instructions

Conventions for working on this project so it stays small, readable, and safe to
extend. If a change conflicts with these notes, update the notes in the same
change.

---

## 1. Golden rules

1. **The API is the contract.** The front end, and any future client, only talks
   to the documented endpoints in [API.md](API.md). Never let a client reach the
   database directly.
2. **Validate on the server, always.** Client-side checks are for UX only. Every
   write path re-validates in `ExpenseIn`.
3. **One source of truth per fact.** Categories live in `app.py: CATEGORIES`.
   The DB schema lives in `db.py: SCHEMA`. Don't duplicate either.
4. **Keep the dependency list tiny.** Runtime deps are `fastapi` + `uvicorn`.
   Adding a third runtime dependency needs a note in [REQUIREMENTS.md](REQUIREMENTS.md)
   (NFR-2) explaining why.
5. **Docs travel with code.** A behaviour change updates `docs/` and the
   `Changelog` sections in the same commit.

---

## 2. Backend (`app.py`, `db.py`)

### Structure

- `db.py` is the **only** module that imports `sqlite3` or knows the schema.
  If you find yourself writing SQL elsewhere, add a function to `db.py` instead.
- Route handlers stay thin: validate (via the Pydantic model) → one or two SQL
  statements → return a dict/model. Business rules that grow beyond a couple of
  lines get their own function.
- Use the `get_conn` dependency for DB access in handlers. Don't open ad-hoc
  connections — you lose the automatic commit/rollback.

### SQL

- **Always parameterise.** `conn.execute("... WHERE id = ?", (id,))`. Never
  f-string user input into SQL.
- Keep statements readable and multi-line. This project favours clarity over
  cleverness.
- Any new query that filters or sorts on a column should have a matching index
  in `SCHEMA` (and a note in [ARCHITECTURE.md](ARCHITECTURE.md) §4).

### Validation

- Add rules as `@field_validator` methods on `ExpenseIn`, returning the cleaned
  value. Raise `ValueError("plain message")` — FastAPI turns it into a `422`
  with that message.
- Keep error messages short, specific, and user-safe (they surface in the UI).

### Status codes

- `201` for create, `200` for update, `204` (no body) for delete, `404` for
  unknown id, `422` for bad input. Don't invent new ones without updating
  [API.md](API.md) §1.1.

### Schema changes / migrations

- `init_db()` only does `CREATE ... IF NOT EXISTS`. It does **not** alter
  existing tables.
- For a change to a populated database, write an explicit migration step
  (a small script or a versioned block) and document:
  1. the DDL, 2. how to back up first (`copy budget.db`), 3. rollback.
- Bump the app `version` in `FastAPI(...)` and add an [API.md](API.md) changelog
  row if the response shape changes.

### Config

- New config goes through an environment variable with a safe default, read in
  one place, and documented in [SETUP.md](SETUP.md) §4. Don't read `os.environ`
  scattered through handlers.

### Time

- Store timestamps in UTC, `YYYY-MM-DDTHH:MM:SSZ`. The "this month" figure is
  computed client-side from the local clock — keep date handling explicit.

---

## 3. Frontend (`index.html`)

- **No build step, no external assets.** Everything (HTML, CSS, JS) stays in the
  one file and loads offline. No CDN scripts, no web fonts.
- **Never** use `innerHTML` / `insertAdjacentHTML` with values that came from the
  API or the user. Build nodes with the `el()` helper and set `textContent`.
  The one `innerHTML` use is `donutSVG()` — it only interpolates numbers and
  `escapeXml()`-ed category labels. Keep it that way; don't add another.
- All network calls go through the `api()` wrapper so error handling and the
  connection banner stay consistent. On failure, show a message; don't leave the
  UI in a half-updated state.
- Keep the in-memory `expenses` array in sync with the server by using the
  **response** of a write (not by guessing) — `POST`/`PUT` return the saved row.
- Theme and currency are the only things allowed in `localStorage`. Expense data
  is never cached there.
- Preserve accessibility: every input keeps its `<label>`; category colour is
  always paired with the text label; respect `prefers-color-scheme`.
- CSS: keep using the custom-property tokens at the top for colours so light/dark
  both keep working. Test both themes and a narrow (~380px) width.

---

## 4. Security

- Treat v1.0 as **localhost-only**. Do not add a default that binds `0.0.0.0`.
- Before any network exposure: add authentication (an `app.py` dependency),
  serve over TLS (reverse proxy), and set an explicit `BUDGET_CORS`.
- Keep parameterised SQL and server-side validation — they are the main
  injection/XSS defences here.
- Never log full request bodies at info level if auth tokens are later added.
- `budget.db` may contain personal financial data — don't commit it, don't ship
  it in backups to shared locations without the user's intent.

---

## 5. Testing

- Run the smoke test in [SETUP.md](SETUP.md) §6 before and after a change to the
  API. It must pass and leave the DB empty.
- When adding an endpoint or a validator, add a matching `curl`/`Invoke-RestMethod`
  line to that smoke test.
- Manually check the UI in Chrome/Edge and Firefox, light and dark, after
  front-end changes.
- If the project grows, promote the smoke test to `pytest` + `fastapi.testclient`
  with a temporary `BUDGET_DB` per test (see [TODO.md](TODO.md)).

---

## 6. Git hygiene

- Respect the `.gitignore` in [SETUP.md](SETUP.md) §5 — no `.venv/`, no
  `budget.db*`, no `server*.log`.
- One logical change per commit; commit message says what and why.
- Update the relevant `docs/` file and its changelog in the same commit as the
  code.
- Keep `requirements.txt` pinned to exact versions.

---

## 7. Style

- **Python:** standard library + FastAPI idioms; type hints on public functions;
  `from __future__ import annotations` is already set. Keep modules short.
  Format with `black`/`ruff` defaults if you introduce a formatter (note it in
  `requirements` as a dev-only dep).
- **JS:** `"use strict"`, `var`/function style already used in the file — match
  it for consistency rather than mixing in `const`/arrow syntax piecemeal.
- **Markdown docs:** keep the header block (status/date/links), use tables for
  reference material, and keep line length reasonable.

---

## 8. Definition of done (for a change)

- [ ] Code works locally; server starts clean; UI unaffected paths still work.
- [ ] Server-side validation covers any new input.
- [ ] Smoke test updated and passing; DB left clean.
- [ ] `docs/` updated (API/REQUIREMENTS/ARCHITECTURE/USER_GUIDE as applicable)
      including changelog rows.
- [ ] No new runtime dependency without a justification note.
- [ ] No secrets, no `budget.db`, no logs committed.
- [ ] [TODO.md](TODO.md) updated (item moved to Done, or new follow-ups added).
