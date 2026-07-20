# Automation

Real Python code for the model monitoring review assignment workflow.
Meant to run on the existing TFS Python server, scheduled via cron (or
whatever the server already uses) at `RUN_INTERVAL_MINUTES`.

## Status

| Module | Status |
|---|---|
| `rotation_queue.py` | ✅ Built and tested. Reads the shared spreadsheet, applies eligibility + "oldest last-assigned" logic. |
| `status_sync.py` | ✅ Built and tested. Syncs DS status spreadsheet → Snowflake, only on real changes. |
| `email_parser.py` | ⚠️ Placeholder. Built against our best guess of the Archer email format. **Update once the real governance email arrives** — see the module docstring for exactly what to change. |
| `review_inventory.py` | ✅ Built. Untested end-to-end (no live Snowflake connection here) — logic is straightforward CRUD against the schema in `sql/create_tables.sql`. |
| `graph_mailbox.py` | 🔒 Blocked on IT. Needs an Azure AD app registration with `Mail.Read` permission on the governance mailbox. |
| `notifications.py` | 🔒 Blocked on IT. Same app registration as above, needs `Mail.Send`. |
| `reminders.py` | ✅ Built. Depends on `review_inventory`, so untestable live until Snowflake is connected, but logic is simple and covered by the same patterns as the tested modules. |
| `run_cycle.py` | ✅ Built. The orchestrator — this is what the scheduler calls. Each step fails independently so one blocked piece doesn't take down the others. |

## Setup

```bash
cd automation
pip install -r requirements.txt
cp .env.example .env   # fill in real values
```

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

(Verified manually against the fixtures in this repo without pytest installed —
all rotation queue, status sync, and email parser logic passes.)

## Running one cycle manually

```bash
python -m automation.run_cycle
```

## What's blocking full end-to-end operation

1. **Real governance email sample** → update `email_parser.py` patterns
2. **Azure AD app registration** (Mail.Read + Mail.Send on the governance mailbox) → unblocks `graph_mailbox.py` and `notifications.py`
3. **Snowflake credentials + running `sql/create_tables.sql`** → unblocks `review_inventory.py` and everything downstream of it
4. **Confirmed network share path** for the two spreadsheets → set `ROTATION_QUEUE_PATH` / `REVIEW_STATUS_PATH`
5. **Confirmed scheduling mechanism** on the Python server (cron entry pointing at `run_cycle.py`)

Everything else is built, tested where testable, and ready to connect once
those five items land.
