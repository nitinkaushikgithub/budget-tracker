# Budget Tracker

Record personal expenses, tag each by category, and see where your money goes.

A static HTML/JS front end talks to a Python **FastAPI** server, which stores
everything in a single **SQLite** database. All data access goes through a
documented REST API, so the same backend can serve other clients later.

```
index.html   ── browser UI (fetch() → /api/…)
app.py       ── FastAPI server: REST API + serves index.html
db.py        ── SQLite connection + schema
budget.db    ── the database file (created automatically on first run)
```

---

## Quick start

```powershell
cd D:\Claude-Training\budget-tracker

# one-time
C:\Users\BunnyPari\anaconda3\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# run
.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:8000> — interactive API docs at
<http://127.0.0.1:8000/docs>. Stop with `Ctrl+C`.

> The base Anaconda `pip` on this machine is broken, so the venv's Python is
> called explicitly above. Full detail in [docs/SETUP.md](docs/SETUP.md).

---

## Documentation

| Doc | What's in it |
|-----|--------------|
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional & non-functional requirements, data model, scope, acceptance criteria, traceability |
| [docs/API.md](docs/API.md) | REST API reference — endpoints, request/response schemas, error shapes, `curl` examples, integration notes |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | How to use the app: adding/editing/deleting, reading the summary, troubleshooting |
| [docs/SETUP.md](docs/SETUP.md) | Install, run, environment-variable config, project layout, smoke test, **integration guide** |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Component/context/sequence/ER diagrams, key decisions and trade-offs, extension points |
| [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) | Contributor conventions, security notes, testing, "definition of done" |
| [docs/TODO.md](docs/TODO.md) | Backlog, known issues / tech debt, decisions pending |

---

## API at a glance

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | Liveness check |
| `GET` | `/api/categories` | Category list (`id`, `label`, `color`) |
| `GET` | `/api/expenses` | List (optional `?category=`, `?month=YYYY-MM`, `?q=`) |
| `POST` | `/api/expenses` | Create `{amount, description, category, date}` → `201` |
| `PUT` | `/api/expenses/{id}` | Full update → `200` / `404` |
| `DELETE` | `/api/expenses/{id}` | Delete → `204` / `404` |

`date` is `YYYY-MM-DD`, `amount` must be `> 0`, `category` must be a known id.
Invalid input → `422` with a `detail` message. Full spec: [docs/API.md](docs/API.md).

---

## Configuration

Environment variables (all optional): `BUDGET_HOST`, `BUDGET_PORT`, `BUDGET_DB`,
`BUDGET_RELOAD`, `BUDGET_CORS`. See [docs/SETUP.md](docs/SETUP.md) §4.

## The database

`budget.db` is a normal SQLite file in this folder. Inspect it with the
`sqlite3` CLI or [DB Browser for SQLite](https://sqlitebrowser.org/). To reset,
stop the server and delete `budget.db` (plus `-wal` / `-shm` if present) — an
empty schema is recreated on the next start.

Theme and currency are the only things kept in the browser (`localStorage`);
all expense data lives in the database.
