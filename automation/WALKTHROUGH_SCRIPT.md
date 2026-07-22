# National Manager Walkthrough — Presenter Script

**Purpose:** Show the full lifecycle of a model monitoring review, starting
from the real Archer notification email, ending with a national manager's
live view of who's assigned what.

**Before you start:** Run the Snowflake cleanup query (see bottom of this
doc) so the table is empty of test data, then run `python -m
automation.walkthrough_demo` once through fully by yourself as a rehearsal.

---

## Where things live (say this out loud early — it grounds the whole demo)

| Thing | Where |
|---|---|
| Governance's email | Sent to a monitored TFS mailbox |
| **Rotation Queue** (who's eligible) | `PRODUCTION_rotation_queue.xlsx` — *(network share path pending IT confirmation)* |
| **Review Status** (DS updates) | `PRODUCTION_review_status.xlsx` — *(network share path pending IT confirmation)* |
| System of record | Snowflake table `EDP_PRD_WSP.VPP_ANALYTICS.REVIEW_INVENTORY` |
| The automation itself | A scheduled Python job, no app, no login screen |

Have both spreadsheets and a Snowsight tab open in separate windows before
you start, so you can flip between them live.

---

## Step 1 — Show the actual trigger

Pull up the real Archer email screenshot (or open it live if you're on your
TFS mailbox). Point out:
- It's an existing, unmodified Archer notification — nothing new for
  governance to do
- It contains just a model name and a start date — no due date, no model
  number (mention the 49-day cycle assumption here if it comes up)

**Say:** "This is the only thing that changes hands from governance. Everything
after this point is automatic."

## Step 2 — Show the Rotation Queue, before anything happens

Open `PRODUCTION_rotation_queue.xlsx`. Point at:
- Real names, real emails, a Last Assigned Date column
- One person with an Unavailable Start/End Date filled in — explain they'll
  be automatically skipped and automatically return, no manager action needed

**Say:** "This is the only file a manager ever touches, and only when someone
joins, leaves, or goes on vacation."

## Step 3 — Run the assignment live

Switch to the terminal and run:
```
python -m automation.walkthrough_demo
```
Let it run through Section 1 (three emails auto-assigned). Pause on the
printed output.

**Say:** "Three different reviews, three different people, picked automatically
based on who's gone longest without one. No one had to decide this."

## Step 4 — Show the override

Continue to Section 2 in the script. Narrate that this is what happens if a
manager needs to swap someone out.

**Say:** "One line of code — in the real system, this will be a cell edit or a
list update, not a support ticket."

## Step 5 — Show the status update flowing through

Continue to Section 3. Open `PRODUCTION_review_status.xlsx` right after —
switch to Excel and show the row that would appear there in production, and
explain the dropdown (Not Started / In Progress / Complete).

**Say:** "The data scientist's entire job is changing one dropdown. Everything
else — syncing to Snowflake, notifying governance — happens on its own."

## Step 6 — Show reminders/escalation

Continue to Section 4. Point out the overdue and due-soon flags.

**Say:** "This is the piece that doesn't exist today. Right now, a missed
deadline is silent until someone happens to check. This makes it impossible
to miss."

*(Be upfront: live email delivery for this step isn't wired up yet — pending
an IT app registration for mailbox access. The logic and the Snowflake
record-keeping are proven; only the final "send the email" step is pending.)*

## Step 7 — Show the final state

Continue to Section 5 — the summary table. Then switch to Snowsight and run:
```sql
SELECT MODEL_NAME, ASSIGNED_DS_NAME, DUE_DATE, STATUS, ASSIGNED_BY
FROM EDP_PRD_WSP.VPP_ANALYTICS.REVIEW_INVENTORY
ORDER BY DUE_DATE;
```

**Say:** "This is what a national manager would actually see — always current,
no one has to ask anyone for a status update."

---

## Cleanup query (run before AND after your rehearsal, and again right before the real thing)

```sql
DELETE FROM EDP_PRD_WSP.VPP_ANALYTICS.REVIEW_INVENTORY
WHERE MODEL_NAME IN ('Service Ops Credit Loss', 'Return Rate Model 2.1 - MFS', 'Recovery Income');

DELETE FROM EDP_PRD_WSP.VPP_ANALYTICS.REVIEW_INVENTORY_AUDIT_LOG
WHERE REVIEW_ID NOT IN (SELECT REVIEW_ID FROM EDP_PRD_WSP.VPP_ANALYTICS.REVIEW_INVENTORY);
```

## If a manager asks...

- **"What if governance's email format changes?"** → The parser is isolated
  to one file; updating it doesn't touch anything else.
- **"What if the automation goes down?"** → Today's process has zero
  automation and zero tracking as the fallback. This can only be a net
  improvement — worst case, it reverts to exactly today's manual process.
- **"Who else can override an assignment?"** → Currently scoped to national
  managers editing the spreadsheet directly — access control can be refined
  once this moves past pilot.
- **"When can this actually go live?"** → Be honest: blocked on the IT
  mailbox app registration, the real network share path, and confirming the
  49-day cycle assumption with governance. Everything else is built and
  tested.
