"""SQLite storage layer for the budget tracker.

One plain file, `budget.db`, sitting next to this module. No ORM: just the
standard-library `sqlite3` driver plus a couple of helpers.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterator

# Location of the database file. Override with the BUDGET_DB environment
# variable (absolute path recommended) when integrating or deploying.
DB_PATH = Path(os.environ.get("BUDGET_DB") or Path(__file__).with_name("budget.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          TEXT PRIMARY KEY,
    amount      REAL NOT NULL CHECK (amount > 0),
    description TEXT NOT NULL,
    category    TEXT NOT NULL,
    date        TEXT NOT NULL,                       -- ISO 'YYYY-MM-DD'
    note        TEXT,                                -- optional free text, <=200 chars, trimmed; NULL when empty
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_expenses_date     ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
"""


def connect() -> sqlite3.Connection:
    """Open a connection with sane defaults (row dicts + FK + WAL)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def get_conn() -> Iterator[sqlite3.Connection]:
    """FastAPI ``yield`` dependency: a per-request connection that always closes.

    Commits on clean exit, rolls back if the handler raised.
    """
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the table and indexes if they do not exist yet."""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
