# Budget Tracker — User Guide

A short guide to using the app day to day. For installing and running it, see
[SETUP.md](SETUP.md).

---

## 1. What it does

Budget Tracker lets you record what you spend, tag each expense with a category,
and see where your money goes through a running total and a donut chart. Your
records are stored in a small database on your computer by a local server, so
they stay put between sessions.

## 2. Opening the app

1. Start the server (see [SETUP.md](SETUP.md) — usually `python app.py`).
2. Open **http://127.0.0.1:8000** in your browser.

If you see a red bar saying *"Can't reach the server"*, the server isn't running
— start it and click **Retry**.

## 3. The screen at a glance

| Area | What it's for |
|------|---------------|
| **Header** | App title, **currency** selector, **theme** button |
| **Add expense** (left) | The entry form |
| **Summary** (right) | Totals and the donut chart |
| **Expenses** (below) | Every record, with filter chips and search |

## 4. Adding an expense

1. In **Add expense**, enter:
   - **Amount** — a number greater than 0 (e.g. `249.50`).
   - **Description** — a short note (up to 120 characters).
   - **Category** — pick from the dropdown.
   - **Date** — defaults to today; change it with the date picker.
2. Click **Add expense**.

The record appears at the top of the **Expenses** list and the summary updates
immediately. The form clears so you can add another.

If something's wrong with the entry (e.g. amount is 0 or blank), the app shows a
message and nothing is saved.

## 5. Editing an expense

1. Find the row in the **Expenses** list.
2. Click **Edit**. The form at the top switches to *"Edit expense"* and fills in
   the current values; the page scrolls up to it.
3. Change what you need and click **Save changes** — or click **Cancel** to back
   out without changing anything.

## 6. Deleting an expense

- **One record:** click **Delete** on its row and confirm.
- **Everything:** click **Delete all** (top-right of the Expenses card) and
  confirm. This removes every record and cannot be undone.

## 7. Finding records

- **Filter by category:** click a category **chip** above the list. Click **All**
  to clear it.
- **Search:** type in the **Search description…** box to show only rows whose
  description contains what you typed.
- The count next to the list header shows *"N of M shown"* when a filter is active.

Filters affect only the list. The **Summary** totals and chart always reflect
*all* your records.

## 8. Reading the summary

| Tile | Meaning |
|------|---------|
| **Total spent** | Sum of every record |
| **This month** | Sum of records dated in the current calendar month |
| **Records** | How many expenses you've logged |
| **Top category** | The category you've spent the most in overall |

The **donut chart** shows each category's share of total spending, and the
**legend** beside it lists every category with its colour, amount and exact
percentage. Each category gets at least a thin visible arc, so its colour still
shows on the ring even when its share is very small — check the legend for the
precise figures. Hover a donut segment to see its label and amount.

## 9. Currency and theme

- **Currency:** the selector in the header switches the symbol shown on every
  amount (₹, $, €, £). It does not convert values — it only changes the symbol.
- **Theme:** the button cycles **System → Light → Dark**. "System" follows your
  operating system's light/dark setting.

Both choices are remembered in *this* browser only. They are **not** part of your
expense data and don't move with the database.

## 10. Where your data lives

- All expenses are stored in a file called **`budget.db`** in the project folder
  (a SQLite database), written by the local server.
- It survives closing the browser, stopping the server, and restarting your PC.
- **Back it up** by copying `budget.db` somewhere safe while the server is
  stopped.
- It is tied to your computer — it does not sync to other devices or browsers.

## 11. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Red *"Can't reach the server"* bar | The server process isn't running. Start it, then click **Retry**. |
| *"Could not save"* / *"Could not delete"* message | The server rejected the request (e.g. invalid value) or dropped mid-request. Check the value and try again; check the server window for errors. |
| Page won't load at all | Wrong address, or another program is using the port. See [SETUP.md](SETUP.md) → *Changing the port*. |
| The calendar icon looked invisible before | Fixed — the date field now follows the light/dark theme. |
| I want to start over | Stop the server, delete `budget.db` (and `budget.db-wal` / `budget.db-shm` if present), start again. A fresh empty database is created. |
| Amounts show the wrong symbol | Change it with the currency selector in the header. |

## 12. Good habits

- Enter expenses as they happen, or set aside a couple of minutes daily — the
  "This month" tile is only as accurate as your entries.
- Use **Other** sparingly; specific categories make the donut chart useful.
- Keep descriptions short but searchable (include a merchant or purpose).
- Copy `budget.db` to backup storage periodically.
