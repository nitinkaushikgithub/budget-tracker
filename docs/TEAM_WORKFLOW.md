# Budget Tracker — Scrum Team Workflow

- **Status:** active as of 2026-09-05
- **Applies to:** the subagents in `.claude/agents/` — `architect-ada`, `lead-rhys`,
  `engineer-nova`, `engineer-kai`, `qa-iris`

---

## 1. The team

| Agent | Persona | Role | Focus |
|-------|---------|------|-------|
| `architect-ada` | Ada | Architect | Design, ADRs, work breakdown. No implementation. |
| `lead-rhys` | Rhys | Lead engineer | Code-review gate, technical arbitration, riskiest task. |
| `engineer-nova` | Nova | Senior engineer | Backend: `app.py`, `db.py`, API, SQLite. |
| `engineer-kai` | Kai | Senior engineer | Frontend: `index.html`, UI, CSS tokens, chart. |
| `qa-iris` | Iris | Senior QA | Independent verification gate before merge. |

## 2. How coordination actually works

Claude Code subagents do **not** hold live peer-to-peer conversations. Each agent runs, does its
job, and returns a report to whoever invoked it. So one session acts as **Scrum Master** — by
default the main Claude Code session you're typing in — and relays artifacts between stages:

```
you ──► Scrum Master (main session)
             │
             ├─► architect-ada        design brief + ADR + numbered work breakdown
             │        ▼
             ├─► engineer-nova / engineer-kai   implement one task each (parallel if independent)
             │        ▼
             ├─► lead-rhys            review each diff → CHANGES REQUESTED ↺ or APPROVED
             │        ▼
             ├─► qa-iris              verify against acceptance criteria → FAIL ↺ or PASS
             │        ▼
             └─► merge (Scrum Master / you)
```

`architect-ada` and `lead-rhys` also hold the `Agent` tool, so they *can* dispatch work down the
tree themselves (e.g. Rhys re-invoking an engineer with a fix list). Results still bubble back up
to the caller — nothing routes sideways on its own.

## 3. The pipeline, stage by stage

1. **Intake (Scrum Master).** Decide size. A one-file, no-API, no-schema tweak can skip Ada — go
   straight to an engineer with written acceptance criteria. Anything touching an endpoint, the
   schema, dependencies, or multiple files starts at Ada.
2. **Design — `architect-ada`.** Produces `docs/adr/NNNN-*.md` and a numbered work breakdown:
   each task has scope, files, testable acceptance criteria, dependencies, size, and a suggested
   owner. Also names what the `docs/SETUP.md` §6 smoke test must gain.
3. **Implement — `engineer-nova` / `engineer-kai`.** One task per invocation, against its
   acceptance criteria. Independent tasks can run as parallel subagents. Each returns a diff, a
   changelog line, updated `docs/TODO.md`, and self-review notes. Smoke test run; DB left clean.
4. **Review — `lead-rhys`.** Checks the diff against `docs/BEST_PRACTICES.md` and runs the smoke
   test. Returns **CHANGES REQUESTED** (numbered, specific — loops back to the engineer) or
   **APPROVED** (short summary, advance to QA). Nothing partial moves forward.
5. **QA — `qa-iris`.** Independent. Runs the full smoke test, every acceptance criterion, edge
   cases (`422`/`404`, both themes, ~380px), and docs/DB hygiene. Returns **FAIL** (minimal
   repro, back to Rhys/engineer) or **PASS** (“cleared to merge” + the exact `git add` paths).
6. **Merge (Scrum Master / you).** Only after Iris's PASS. One logical change per commit; the
   commit includes the code, the docs update, and the `docs/TODO.md` move.

## 4. Definition of done (unchanged from `docs/BEST_PRACTICES.md` §8)

- Code works locally; server starts clean; unaffected paths still work.
- Server-side validation covers any new input.
- Smoke test updated and passing; DB left clean.
- `docs/` updated (API / REQUIREMENTS / ARCHITECTURE / USER_GUIDE as applicable) incl. changelog.
- No new runtime dependency without a justification note.
- No secrets, no `budget.db`, no logs committed.
- `docs/TODO.md` updated.

## 5. Invoking the team

- Auto: describe the work to the main session; it routes to `architect-ada` for anything
  architectural, or straight to an engineer for a small change.
- Explicit: `use the architect-ada subagent to design …`, `use lead-rhys to review …`,
  `use qa-iris to verify …`.
- To continue a specific agent with its context intact, message it by name rather than spawning a
  fresh one.
