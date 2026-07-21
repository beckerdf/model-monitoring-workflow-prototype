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
| `graph_mailbox.py` | ⚠️ Updated to delegated auth (DB's own mailbox, sign in once via device code). Still needs an Azure AD app registration for `Mail.Read`/`Mail.Send` as **delegated** permissions — smaller ask than app-only, may not need IT/admin approval depending on tenant policy. |
| `notifications.py` | ⚠️ Same as above — sends from DB's own mailbox for now. |
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
2. **Azure AD app registration for delegated `Mail.Read`/`Mail.Send`** on DB's own mailbox → unblocks `graph_mailbox.py` and `notifications.py`. Check whether this needs IT approval or can be self-service — delegated, single-mailbox scope is a much smaller ask than the originally-scoped shared-mailbox/app-only version.
3. **Snowflake credentials + running `sql/create_tables.sql`** → unblocks `review_inventory.py` and everything downstream of it
4. **Confirmed network share path** for the two spreadsheets → set `ROTATION_QUEUE_PATH` / `REVIEW_STATUS_PATH`
5. **Confirmed scheduling mechanism** on the Python server (cron entry pointing at `run_cycle.py`)

**Note on the mailbox approach:** this currently runs through DB's own TFS mailbox rather than a dedicated shared governance mailbox, to avoid requesting a new mailbox be created. Governance would need to send/CC assignment emails to DB's address for this to pick them up. If a shared mailbox is set up later, `graph_mailbox.py` and `notifications.py` would need to revert to the app-only pattern (client credentials, no per-user sign-in) so the automation doesn't depend on one person's login.

Everything else is built, tested where testable, and ready to connect once
those five items land.
