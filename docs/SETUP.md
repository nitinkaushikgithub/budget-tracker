# Budget Tracker — Setup, Run & Integration

Covers installing dependencies, running the server, configuration, project
layout, testing, and integrating the API with other software.

---

## 1. Prerequisites

- **Python 3.9+** (developed and verified on CPython **3.12.4**).
- Ability to create a virtual environment and install two packages
  (`fastapi`, `uvicorn`).
- A modern browser for the UI.

> **This machine's quirk:** the base Anaconda install at
> `C:\Users\BunnyPari\anaconda3` has a **broken `pip`**
> (`ModuleNotFoundError: No module named 'pip._internal.utils.temp_dir'`).
> The steps below use a project-local virtual environment, whose own `pip`
> works. Always call the venv's Python explicitly:
> `.venv\Scripts\python.exe`.

---

## 2. First-time setup

```powershell
cd D:\Claude-Training\budget-tracker

# create the virtual environment (uses the Anaconda base Python as the seed)
C:\Users\BunnyPari\anaconda3\python.exe -m venv .venv

# install runtime dependencies into the venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` pins:

```
fastapi==0.115.6
uvicorn==0.34.0
```

Verify:

```powershell
.venv\Scripts\python.exe -c "import fastapi, uvicorn; print(fastapi.__version__, uvicorn.__version__)"
```

---

## 3. Running the server

```powershell
cd D:\Claude-Training\budget-tracker
.venv\Scripts\python.exe app.py
```

- UI: <http://127.0.0.1:8000>
- Swagger docs: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>
- Stop with `Ctrl+C`.

On first start the server creates `budget.db` with the schema from `db.py`.

### Run in the background (PowerShell)

```powershell
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "app.py" `
  -RedirectStandardOutput "server.out.log" -RedirectStandardError "server.err.log" -WindowStyle Hidden
```

Stop it:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

---

## 4. Configuration (environment variables)

All optional. Set them before starting `app.py`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BUDGET_HOST` | `127.0.0.1` | Interface to bind. Use `0.0.0.0` to accept LAN connections **(only with auth/TLS added — see §7)**. |
| `BUDGET_PORT` | `8000` | TCP port. |
| `BUDGET_DB` | `./budget.db` | Path to the SQLite file. Use an absolute path when integrating or running as a service. |
| `BUDGET_RELOAD` | *(unset)* | Any non-empty value enables Uvicorn auto-reload (development only). |
| `BUDGET_CORS` | *(unset)* | Comma-separated list of browser origins allowed to call the API cross-origin. |

**PowerShell example**

```powershell
$env:BUDGET_PORT = "9000"
$env:BUDGET_DB   = "D:\Claude-Training\budget-tracker\data\budget.db"
$env:BUDGET_CORS = "http://localhost:5173"
.venv\Scripts\python.exe app.py
```

**bash example**

```bash
BUDGET_PORT=9000 BUDGET_DB=/srv/budget/budget.db python app.py
```

### Changing the port

If `8000` is taken (`[Errno 10048] address already in use`), set `BUDGET_PORT`
to a free port, or find and stop the process using `8000`:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object OwningProcess
```

---

## 5. Project layout

```
budget-tracker/
├── app.py              # FastAPI app: routes, validation, serves index.html
├── db.py               # SQLite connection helpers + schema (init_db)
├── index.html          # Single-file web UI (HTML + CSS + vanilla JS)
├── requirements.txt    # Pinned runtime dependencies
├── budget.db           # SQLite database (created at runtime; not in source control)
├── README.md           # Entry point / quick start
├── server.out.log      # stdout when run in background (runtime artifact)
├── server.err.log      # stderr / Uvicorn logs (runtime artifact)
├── .venv/              # Virtual environment (not in source control)
└── docs/
    ├── REQUIREMENTS.md
    ├── API.md
    ├── USER_GUIDE.md
    ├── SETUP.md            # this file
    ├── ARCHITECTURE.md
    ├── BEST_PRACTICES.md
    └── TODO.md
```

### Suggested `.gitignore`

```
.venv/
__pycache__/
*.pyc
budget.db
budget.db-wal
budget.db-shm
server.out.log
server.err.log
```

---

## 6. Smoke test

With the server running, this exercises every endpoint and leaves the database
empty.

```powershell
$base = "http://127.0.0.1:8000/api"
$J = 'application/json'

$a = Invoke-RestMethod "$base/expenses" -Method Post -ContentType $J -Body '{"amount":249.5,"description":"Weekly groceries","category":"groceries","date":"2026-09-01"}'
$b = Invoke-RestMethod "$base/expenses" -Method Post -ContentType $J -Body '{"amount":60,"description":"Metro card","category":"transport","date":"2026-09-02"}'

Invoke-RestMethod "$base/expenses"                             # list (2 rows, newest first)
Invoke-RestMethod "$base/expenses?category=transport"          # filter
Invoke-RestMethod "$base/expenses/$($a.id)" -Method Put -ContentType $J -Body '{"amount":300.75,"description":"Groceries fixed","category":"food","date":"2026-09-01"}'
Invoke-WebRequest  "$base/expenses/$($a.id)" -Method Delete -UseBasicParsing   # 204
Invoke-WebRequest  "$base/expenses/$($b.id)" -Method Delete -UseBasicParsing   # 204

Invoke-RestMethod "$base/expenses"                             # [] empty
```

Expected: POST → `201`, PUT → `200`, DELETE → `204`, invalid bodies → `422`,
unknown id → `404`.

### Inspecting the database directly

```powershell
@'
import sqlite3
c = sqlite3.connect("budget.db")
for row in c.execute("SELECT date, category, amount, description FROM expenses ORDER BY date DESC"):
    print(row)
'@ | Set-Content _peek.py -Encoding utf8
.venv\Scripts\python.exe _peek.py
Remove-Item _peek.py
```

Or use a GUI such as [DB Browser for SQLite](https://sqlitebrowser.org/).

### Resetting all data

```powershell
# stop the server first
Remove-Item budget.db, budget.db-wal, budget.db-shm -ErrorAction SilentlyContinue
# next start recreates an empty schema
```

---

## 7. Integration guide

### 7.1 Call the API from another application

The API is plain JSON over HTTP (see [API.md](API.md)). Minimal client flow:

1. `GET /api/categories` once, cache it (id → label/colour).
2. `GET /api/expenses` (optionally with `?category`, `?month`, `?q`) to read.
3. `POST /api/expenses` to add, `PUT /api/expenses/{id}` to change,
   `DELETE /api/expenses/{id}` to remove.
4. Treat `422` as "bad payload" (read `detail[].msg`), `404` as "unknown id".

**Browser client on a different origin** — start the server with
`BUDGET_CORS` listing that origin, e.g.:

```powershell
$env:BUDGET_CORS = "http://localhost:5173,https://myapp.example"
.venv\Scripts\python.exe app.py
```

**Generate a typed client** from `GET /openapi.json` with your language's
OpenAPI generator — it always matches the running server.

### 7.2 Point at a different database location

Set `BUDGET_DB` to an absolute path. The parent directory must exist. Example:
keep data outside the code tree so a redeploy never risks it:

```powershell
$env:BUDGET_DB = "D:\data\budget\budget.db"
```

### 7.3 Swap SQLite for another engine (e.g. PostgreSQL)

`db.py` is the only module that touches storage. To migrate:

1. Replace `connect()` / `get_conn()` with the new driver (e.g. `psycopg`),
   keeping the same function names and the `row_factory`-style dict rows.
2. Port `SCHEMA` to the new dialect (`SERIAL`/`UUID`, `TIMESTAMPTZ`, etc.).
3. Adjust the SQL in `app.py` if needed (`substr(date,1,7)` for the month
   filter is standard SQL and should port unchanged).
4. Update [REQUIREMENTS](REQUIREMENTS.md) NFR-2 and this doc.

The API contract and the front end do not change.

### 7.4 Run as a long-lived service

- Use a process manager (Windows: NSSM / Task Scheduler; Linux: systemd).
- Set `BUDGET_HOST`, `BUDGET_PORT`, `BUDGET_DB` explicitly.
- **Do not expose it beyond localhost without adding authentication and TLS**
  (v1.0 has neither — see [REQUIREMENTS](REQUIREMENTS.md) NFR-7). Put it behind a
  reverse proxy (Caddy/Nginx) that terminates TLS and enforces auth, or add an
  auth dependency in `app.py`.
- For multiple worker processes, run `uvicorn app:app --workers N` — SQLite in
  WAL mode handles concurrent readers; keep writes light or move to a client/
  server database (§7.3).

### 7.5 Backups

`budget.db` is a single file. Copy it while the server is stopped, or use
SQLite's online backup API / `VACUUM INTO 'backup.db'` while it runs.

---

## 8. Uninstall

Stop the server, then delete the `budget-tracker` folder. Nothing is installed
system-wide; the virtual environment and database live entirely inside it.
