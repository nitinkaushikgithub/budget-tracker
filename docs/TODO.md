# Budget Tracker — TODO / Backlog

Working list. Keep it honest: move items to **Done** with a date, add follow-ups
as they appear. Priorities: **P1** now/next · **P2** soon · **P3** nice-to-have.

---

## Done

| Date | Item |
|------|------|
| 2026-09-03 | Initial UI: add/edit/delete, category dropdown, donut summary + legend, filters, search |
| 2026-09-03 | Donut: added a minimum visible arc per category so small categories still show their colour (legend keeps exact %) |
| 2026-09-03 | Fixed connection notice that could never hide (`.banner` display overrode `hidden`); added `[hidden]{display:none!important}`; toned it from a red block to a subtle pill |
| 2026-09-03 | Server sends `Cache-Control: no-cache` for `index.html` so redeploys are picked up without a hard refresh |
| 2026-09-03 | Git repo initialised (branch `main`) with `.gitignore` + `.gitattributes`; initial commit |
| 2026-09-03 | Light/dark/system theme; fixed invisible date-picker icon via `color-scheme` |
| 2026-09-03 | Currency selector (₹/$/€/£) |
| 2026-09-03 | Replaced browser `localStorage` storage with **SQLite + FastAPI REST API** |
| 2026-09-03 | `db.py` schema bootstrap, WAL, indexes on `date` + `category` |
| 2026-09-03 | Server-side validation (amount > 0, known category, `YYYY-MM-DD`, non-empty description) |
| 2026-09-03 | Env config: `BUDGET_HOST` / `BUDGET_PORT` / `BUDGET_DB` / `BUDGET_RELOAD` / `BUDGET_CORS` |
| 2026-09-03 | Connection-error banner + `api()` fetch wrapper in the UI |
| 2026-09-03 | Docs: REQUIREMENTS, API, USER_GUIDE, SETUP, ARCHITECTURE, BEST_PRACTICES, TODO |

---

## P1 — now / next

- [ ] **Optional expense `note`** (ADR [0001](adr/0001-optional-expense-note.md),
      branch `demo/expense-note`). Task 1 done: `note` on the model + `SCHEMA`
      (fresh DBs) + `INSERT`/`UPDATE` + API bumped to v1.1.0 + docs. Task 2 done:
      one-time populated-DB migration documented in
      [MIGRATIONS.md](MIGRATIONS.md) §1 (`ALTER TABLE expenses ADD COLUMN note
      TEXT`, reversible), linked from SETUP.md §6/§7. Task 3 done: UI note field
      in the add/edit form + muted line under the description + USER_GUIDE
      §3–§5. All three tasks complete — ready for QA.
- [ ] **Automated tests.** `pytest` + `fastapi.testclient`; each test gets a
      temp `BUDGET_DB`. Cover: CRUD happy paths, every validator (`422`),
      `404` on unknown id, list filters (`category` / `month` / `q`).
- [ ] **Push to a remote.** Repo is initialised locally (branch `main`); add a
      GitHub/GitLab remote and push when ready.
- [ ] **Currency is a real setting, not just a symbol.** Decide: keep as
      display-only (document it clearly in the UI) *or* store an ISO currency
      code per record and format with `Intl.NumberFormat`.
- [ ] **Confirm "Delete all" cost.** It fires N sequential `DELETE`s. If lists
      get large, add `DELETE /api/expenses` (guarded) — update
      [API.md](API.md) if so.

## P2 — soon

- [ ] **Server-side summary endpoint.** `GET /api/summary?month=YYYY-MM` →
      totals, per-category breakdown, top category. Lets other clients skip
      re-implementing the maths; UI can switch to it.
- [ ] **Pagination / range on `GET /api/expenses`.** `limit` + `offset` or
      `before`/`after` cursors; keep "all" as default for small data.
- [ ] **Money precision.** Migrate `amount` from `REAL` to integer minor units
      (store paise/cents) to remove float rounding. Needs a data migration +
      API note (values stay decimal in JSON).
- [ ] **`PATCH /api/expenses/{id}`** for partial updates (UI currently always
      sends all fields via `PUT`).
- [ ] **Extend `q` to match notes.** `GET /api/expenses?q=` currently matches
      `description` only; include the new `note` column (ADR 0001 §4). Needs the
      `LIKE` clause widened in `list_expenses`; note stays unindexed.
- [ ] **Date range filter** in the API (`from` / `to`) and matching UI control.
- [ ] **Export** (CSV / JSON) endpoint — deferred by product decision earlier;
      revisit only if the user asks. If added, it's an API endpoint, not a
      browser-only feature.
- [ ] **Structured logging** (JSON lines) + a `--log-level` / `BUDGET_LOG_LEVEL`.

## P3 — nice to have

- [ ] **Budgets / limits per category** with progress vs. actual on the summary.
- [ ] **Recurring expenses** (templates the user can post with one click).
- [ ] **Multi-currency with conversion** (rates source + base currency).
- [ ] **Undo** for delete (soft-delete column + a short-lived "Undo" toast).
- [ ] **Keyboard-first entry** (focus amount on load, `Enter` to submit, `Esc`
      to cancel edit).
- [ ] **PWA / offline queue** — queue writes when the server is unreachable and
      flush on reconnect.
- [ ] **Dockerfile / compose** for one-command run.
- [ ] **Charts over time** (monthly spend trend line).

---

## Needs a decision (blocked on product intent)

- **Auth model.** None today (localhost only). If this ever runs on a network:
  single shared password? per-user accounts? external proxy auth? — drives
  whether we need a `users` table.
- **Database engine.** SQLite is the right call for local single-user. Move to
  PostgreSQL only if multi-user / networked becomes a goal (see
  [SETUP.md](SETUP.md) §7.3).
- **Category management.** Keep the fixed code list, or let users add/rename/
  recolour categories (needs a `categories` table + referential integrity +
  handling of in-use categories on delete).

---

## Known issues / tech debt

- `amount` stored as floating point (see P2 "Money precision").
- No `updated_at` sub-second resolution — rapid edits in the same second show
  an unchanged timestamp. Cosmetic.
- "Delete all" is not atomic (N requests); a mid-way failure leaves a partial
  delete. UI reloads the list from the server on error to resync.
- No automated tests yet (P1).
- Front end keeps a full in-memory copy of all expenses; fine for personal
  scale, revisit with pagination (P2).
