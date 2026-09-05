# Budget Tracker — Database Migrations

`init_db()` only ever runs `CREATE TABLE / CREATE INDEX ... IF NOT EXISTS`
(see [BEST_PRACTICES.md](BEST_PRACTICES.md) §2, [ARCHITECTURE.md](ARCHITECTURE.md)).
It **never `ALTER`s an existing table**. A fresh `budget.db` always gets the
current schema from `db.py: SCHEMA`; an **already-populated** `budget.db` needs
the one-time manual step below whenever a release adds or changes a column.

All commands are PowerShell and call the venv's Python explicitly
(`.venv\Scripts\python.exe`) per [CLAUDE.md](../CLAUDE.md) — never bare
`python` / `pip`. Run them from the repo root
(`D:\Claude-Training\budget-tracker`).

> If you do **not** have an existing `budget.db` — or you are happy to discard
> it — you do not need any of this: stop the server, delete `budget.db`,
> `budget.db-wal`, `budget.db-shm` (SETUP.md §6 "Resetting all data"), and the
> next start builds the current schema empty.

---

## 1. Migration 0001 — add `expenses.note` (API v1.1.0, branch `demo/expense-note`)

Adds a nullable free-text `note` column to `expenses`. Background and rationale:
[ADR 0001](adr/0001-optional-expense-note.md) §3 and §"Rollback".

- **Column definition:** `note TEXT` — nullable, **no default**, no `CHECK`.
  Existing rows read back `note = NULL`.
- **Position caveat:** on a fresh DB the `SCHEMA` places `note` mid-table
  (between `date` and `created_at`). `ALTER TABLE ... ADD COLUMN` always
  **appends** it as the last column. All code accesses columns by name, so this
  is purely cosmetic — but `PRAGMA table_info(expenses)` will list `note` in a
  different position on a migrated DB than on a fresh one. Not a bug.
- **Reversible:** yes — restore the backup (primary), or `DROP COLUMN` on
  SQLite ≥ 3.35 (alternative).

### 1.1 Procedure

**Step 1 — Stop the server.**
`Ctrl+C` in its window, or if it runs in the background (SETUP.md §3):

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Nothing may hold the database open while you migrate.

**Step 2 — Back up the database file.**

```powershell
Copy-Item budget.db budget.db.bak
# If the WAL sidecar files are present, copy them too (a clean shutdown usually
# checkpoints and removes them; copy whatever exists):
Copy-Item budget.db-wal budget.db-wal.bak -ErrorAction SilentlyContinue
Copy-Item budget.db-shm budget.db-shm.bak -ErrorAction SilentlyContinue
```

Keep `budget.db.bak` until you have confirmed the migrated server works.

**Step 3 — Inspect the current columns (decide: migrate or abort).**

```powershell
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('budget.db'); [print(r[1], r[2], 'NOTNULL' if r[3] else 'nullable', 'dflt=%r' % r[4]) for r in c.execute('PRAGMA table_info(expenses)')]; c.close()"
```

- If `note` is **not** in the list → continue to Step 4.
- If `note` **is** already listed → this DB is already migrated. **Stop here.**
  Re-running the `ADD COLUMN` below fails with
  `sqlite3.OperationalError: duplicate column name: note` and changes nothing,
  so it is safe to abort and retry, but there is nothing to do.

**Step 4 — Apply the migration.**

The single DDL statement is:

```sql
ALTER TABLE expenses ADD COLUMN note TEXT;
```

Run it via the venv Python. This helper re-checks `table_info` first, so it is
safe to run twice (it aborts cleanly on the second run):

```powershell
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('budget.db'); cols=[r[1] for r in c.execute('PRAGMA table_info(expenses)')]; (print('ABORT: note already present, nothing to do') if 'note' in cols else (c.execute('ALTER TABLE expenses ADD COLUMN note TEXT'), c.commit(), print('OK: added expenses.note'))); c.close()"
```

**Step 5 — Verify.**

```powershell
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('budget.db'); print('columns:'); [print(' ', r[1], r[2], 'NOTNULL' if r[3] else 'nullable', 'dflt=%r' % r[4]) for r in c.execute('PRAGMA table_info(expenses)')]; n=c.execute('SELECT count(*) FROM expenses').fetchone()[0]; nn=c.execute('SELECT count(*) FROM expenses WHERE note IS NOT NULL').fetchone()[0]; print('rows total:', n, '| rows with a non-NULL note:', nn); c.close()"
```

Expected:

- `note TEXT nullable dflt=None` appears in the column list (last position — see
  the position caveat above).
- `rows total` matches your pre-migration row count (no rows lost).
- `rows with a non-NULL note` is `0` — every pre-existing row has `note = NULL`.

**Step 6 — Start the server and run the smoke test.**

```powershell
.venv\Scripts\python.exe app.py
```

It must start without error and serve the existing rows (now each with
`"note": null`). Then run the [SETUP.md §6](SETUP.md#6-smoke-test) smoke test —
it must pass end to end and leave the database empty of the rows *it* created.

**Step 7 — Clean up.** Once the migrated server is confirmed good, delete the
backups you no longer need (`budget.db.bak`, `budget.db-wal.bak`,
`budget.db-shm.bak`). Keep them if you want a restore point for a while.

### 1.2 Rollback

**Primary — restore the backup** (no data loss: no pre-existing row had a note):

```powershell
# stop the server first (Step 1 above)
Remove-Item budget.db-wal, budget.db-shm -ErrorAction SilentlyContinue
Copy-Item budget.db.bak budget.db -Force
```

**Alternative — drop the column** (SQLite **≥ 3.35** only). Check the version
first:

```powershell
.venv\Scripts\python.exe -c "import sqlite3; print(sqlite3.sqlite_version)"
```

If it prints `3.35.0` or higher:

```sql
ALTER TABLE expenses DROP COLUMN note;
```

```powershell
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('budget.db'); v=tuple(map(int, sqlite3.sqlite_version.split('.'))); print('need SQLite >= 3.35 for DROP COLUMN, have', sqlite3.sqlite_version) if v < (3,35,0) else (c.execute('ALTER TABLE expenses DROP COLUMN note'), c.commit(), print('OK: dropped expenses.note')); c.close()"
```

Below 3.35 there is no `DROP COLUMN`; use the backup restore, or rebuild the
table (create-copy-drop-rename) — unnecessary here since the primary path is a
file copy.

After either rollback, also revert the code (`git checkout main` / revert the
`demo/expense-note` branch). Old code against a DB that still has the `note`
column is harmless: `response_model=Expense` without the field just drops the
extra key.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-09-05 | Created. Migration 0001: `ALTER TABLE expenses ADD COLUMN note TEXT` for populated DBs (ADR 0001, API v1.1.0). |
