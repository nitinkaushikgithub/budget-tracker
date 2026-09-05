"""Budget Tracker API.

Run:
    .venv\\Scripts\\python.exe app.py
then open http://127.0.0.1:8000

Interactive API docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import datetime as dt
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from db import get_conn, init_db

HERE = Path(__file__).parent
INDEX_HTML = HERE / "index.html"

# Single source of truth for categories (id + display label + chart colour).
CATEGORIES = [
    {"id": "food",          "label": "Food & Dining",  "color": "#4e79a7"},
    {"id": "groceries",     "label": "Groceries",      "color": "#59a14f"},
    {"id": "transport",     "label": "Transport",      "color": "#f28e2b"},
    {"id": "housing",       "label": "Housing & Rent", "color": "#e15759"},
    {"id": "utilities",     "label": "Utilities",      "color": "#76b7b2"},
    {"id": "entertainment", "label": "Entertainment",  "color": "#b07aa1"},
    {"id": "health",        "label": "Health",         "color": "#edc948"},
    {"id": "shopping",      "label": "Shopping",       "color": "#ff9da7"},
    {"id": "education",     "label": "Education",       "color": "#9c755f"},
    {"id": "other",         "label": "Other",          "color": "#bab0ac"},
]
CATEGORY_IDS = {c["id"] for c in CATEGORIES}

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Budget Tracker API", version="1.1.0", lifespan=lifespan)

# Same-origin by default (the API serves index.html itself). To call this API
# from a front end on another origin, set BUDGET_CORS to a comma-separated list
# of allowed origins, e.g. BUDGET_CORS="http://localhost:5173,http://localhost:3000".
_cors_origins = [o.strip() for o in os.environ.get("BUDGET_CORS", "").split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #
class ExpenseIn(BaseModel):
    amount: float
    description: str
    category: str
    date: str
    note: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def _amount_positive(cls, v: float) -> float:
        if not (v > 0):
            raise ValueError("amount must be greater than 0")
        return round(float(v), 2)

    @field_validator("description")
    @classmethod
    def _desc_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description is required")
        return v[:120]

    @field_validator("category")
    @classmethod
    def _category_known(cls, v: str) -> str:
        if v not in CATEGORY_IDS:
            raise ValueError(f"unknown category: {v!r}")
        return v

    @field_validator("date")
    @classmethod
    def _date_iso(cls, v: str) -> str:
        try:
            dt.date.fromisoformat(v)
        except ValueError:
            raise ValueError("date must be 'YYYY-MM-DD'")
        return v

    @field_validator("note")
    @classmethod
    def _note_clean(cls, v: Optional[str]) -> Optional[str]:
        # Pydantic runs this for an explicit null but not for an omitted field.
        if v is None:
            return None
        v = v.strip()
        return v[:200] or None


class Expense(ExpenseIn):
    id: str
    created_at: str
    updated_at: str


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/categories")
def list_categories() -> list[dict]:
    return CATEGORIES


@app.get("/api/expenses", response_model=list[Expense])
def list_expenses(
    category: Optional[str] = Query(None),
    month: Optional[str] = Query(None, description="Filter by 'YYYY-MM'"),
    q: Optional[str] = Query(None, description="Substring match on description"),
    conn=Depends(get_conn),
) -> list[dict]:
    sql = "SELECT * FROM expenses WHERE 1=1"
    args: list = []
    if category:
        sql += " AND category = ?"
        args.append(category)
    if month:
        sql += " AND substr(date, 1, 7) = ?"
        args.append(month)
    if q:
        sql += " AND lower(description) LIKE ?"
        args.append(f"%{q.lower()}%")
    sql += " ORDER BY date DESC, created_at DESC"
    return [dict(r) for r in conn.execute(sql, args).fetchall()]


@app.post("/api/expenses", response_model=Expense, status_code=201)
def create_expense(payload: ExpenseIn, conn=Depends(get_conn)) -> dict:
    new_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO expenses (id, amount, description, category, date, note) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (new_id, payload.amount, payload.description, payload.category, payload.date, payload.note),
    )
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (new_id,)).fetchone()
    return dict(row)


@app.put("/api/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: str, payload: ExpenseIn, conn=Depends(get_conn)) -> dict:
    exists = conn.execute(
        "SELECT 1 FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="expense not found")
    conn.execute(
        "UPDATE expenses SET amount = ?, description = ?, category = ?, date = ?, note = ?, "
        "updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
        (payload.amount, payload.description, payload.category, payload.date, payload.note, expense_id),
    )
    row = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    return dict(row)


@app.delete("/api/expenses/{expense_id}", status_code=204, response_class=Response)
def delete_expense(expense_id: str, conn=Depends(get_conn)) -> Response:
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="expense not found")
    return Response(status_code=204)


@app.get("/")
def index() -> FileResponse:
    # no-cache: always revalidate so a redeployed index.html is picked up immediately
    return FileResponse(INDEX_HTML, headers={"Cache-Control": "no-cache"})


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=os.environ.get("BUDGET_HOST", "127.0.0.1"),
        port=int(os.environ.get("BUDGET_PORT", "8000")),
        reload=bool(os.environ.get("BUDGET_RELOAD")),
    )
