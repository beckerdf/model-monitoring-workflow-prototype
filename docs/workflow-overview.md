# Model Monitoring Review Assignment — Automated Workflow

## Current State (Problem)

**Process today:**
1. Model Governance sends an email to Data Science National Managers when a model monitoring review is due
2. National Manager manually reads the email and manually selects a Data Scientist to complete the review
3. National Manager tells the DS via email (or verbally) — no system of record created
4. Data Scientist completes the review in Archer by the due date

**Breakdown points:**
- No tracking mechanism beyond individual managers' email inboxes
- No automatic distribution — fully manual, dependent on one person remembering
- No visibility into who has how many open reviews (workload imbalance risk)
- No due date monitoring — nothing flags an approaching or missed deadline
- No follow-up loop — manager has no way to confirm the review was actually completed correctly, or at all, without manually checking Archer or emailing the DS
- Single point of failure: if the National Manager is out, forgets, or the email is missed, the review can silently slip

**Risk:** Missed model monitoring due dates are a regulatory/governance exposure, not just an internal inconvenience.

---

## Future State (Proposed Workflow)

**Guiding principle:** Governance's existing Archer-generated email becomes the single, consistent trigger. Everything downstream is automated except two human touchpoints: the DS completing the actual review work, and the National Manager's optional override.

### Swimlanes / Roles
- **Model Governance** — sends the standardized Archer-generated email (no change to their process)
- **Automation Layer** (Python job, scheduled on the existing Python server) — reads the spreadsheet and mailbox, parses, assigns, tracks, notifies
- **Rotation Queue** (shared spreadsheet) — where managers make the rare edit; automation reads it, never writes to it
- **Review Status Updates** (shared spreadsheet) — where the DS marks status; automation reads it and syncs into Snowflake
- **Review Inventory** (Snowflake table) — system of record for every review, written entirely by automation
- **National Manager** — owns keeping the spreadsheet accurate (active/inactive, unavailable date ranges); otherwise passive by default, receives the digest and can check the dashboard, active only for overrides and overdue escalations
- **Data Scientist** — receives assignment, performs review in Archer, updates status

### National Manager Responsibility: Rotation Queue Maintenance
The automation is only as accurate as the pool it's assigning from. National Managers keep a shared spreadsheet current, on an ongoing basis:
- **Add** a Data Scientist when onboarded/ready to take reviews
- **Deactivate** a Data Scientist who leaves the team or role
- **Set unavailable dates** for planned absences (e.g., vacation) — manager enters a start and end date directly in the spreadsheet; the automation checks these dates on every run and skips that person for any review triggered within that window, no manual toggle needed before or after
This is a direct edit to a file the manager already knows how to use — no new tool to learn. Because the job reads the spreadsheet fresh on every run, any update a manager makes — including unavailable dates — is reflected on the very next assignment automatically, and the person returns to rotation on their own the day after the end date with no manager action required.

### Step-by-Step Flow

1. **Trigger** — Governance sends the standardized Archer-generated email to a shared/dedicated inbox
2. **Parse** — Scheduled Python job (running on the existing Python server) reads the mailbox via Microsoft Graph API, extracts: model name, review ID, due date
3. **Assign** — Job reads the shared Rotation Queue spreadsheet for the next Data Scientist in line (round-robin), skipping anyone whose unavailable date range covers the current date (e.g., PTO)
4. **Log** — Job inserts a new record into the Snowflake Review Inventory table: model, assigned DS, due date, status = *Not Started*, date assigned
5. **Notify** — Job sends an email (via Graph API/SMTP) to the assigned DS with review details and due date; CCs the National Manager and DB for visibility
6. **(Optional) Override** — National Manager edits the "assigned to" cell directly in the spreadsheet for that review if needed (e.g., DS is on vacation); next automation run picks up the change, triggers a reassignment notification, and keeps the rotation logic consistent
7. **Work performed** — DS completes the model monitoring review in Archer, then updates a Status column directly in the shared Review Status spreadsheet (Not Started → In Progress → Complete). The next automation run reads that change and syncs it into the Snowflake Review Inventory — same low-friction pattern as the manager's rotation queue edits, no new tool for the DS to learn, and Snowflake stays the single source of truth
8. **Automated reminders** — Scheduled job checks open items daily:
   - 7 days before due: reminder to DS
   - 2 days before due: reminder to DS, CC National Manager and DB
   - Past due: escalation email to National Manager and DB, flagged overdue
9. **Closure loop** — When marked Complete, job optionally notifies Governance (or National Manager and DB) that the review is done, closing the loop that's currently missing
10. **Visibility** — Managers get a scheduled email digest (daily/periodic summary of assignments, due soon, overdue) plus an always-current dashboard/report on the Snowflake table for on-demand checking — no login to a custom tool required for either

---

## System of Record: What Lives Where

| Component | Tool | Purpose |
|---|---|---|
| Rotation Queue | Shared spreadsheet (Excel, synced location) | Where managers edit active/inactive and unavailable dates directly |
| Review Status Updates | Shared spreadsheet (Excel, synced location) | Where the DS marks a review Not Started / In Progress / Complete — automation syncs it into Snowflake |
| Review Inventory | Snowflake table | System of record for every review: model, DS, due date, status, dates — written entirely by automation, never edited by hand |
| Automation logic | Python job, scheduled on the existing Python server | Reads spreadsheet + mailbox, parses email, assigns, updates Snowflake, notifies, reminds, escalates |
| Visibility — passive | Scheduled email digest | Daily/periodic summary of current assignments, due soon, overdue — no login needed |
| Visibility — on demand | Live dashboard/report on Snowflake | Always-current view managers can check anytime, no editing |
| Process documentation | Confluence | Runbook / reference doc for how the workflow operates (org standard) |
| Code & CI/CD | GitHub | Version-controlled automation scripts, GitHub Actions pipeline |

**Note:** No custom app required. Managers' only touchpoint is editing the shared spreadsheet for the rare override or unavailability update — everything else is automated push (digest) or passive pull (dashboard). Email access will go through Microsoft Graph API — **interim setup: DB's own TFS mailbox, using delegated auth (DB signs in once), rather than a dedicated shared governance mailbox** — this avoids requesting a new mailbox be created, and needs a smaller ask of IT (delegated, single-mailbox permission vs. app-only access to any mailbox in the tenant). Governance would need to send/CC assignment emails to DB's address for this to work. Revisit if a shared mailbox becomes available later.

---

## Accountability Layers (addresses the "no follow-up" gap directly)

1. **Before due date** — DS is reminded automatically, no manager action needed
2. **Approaching due date** — Manager is looped in automatically as a backstop
3. **After due date** — Manager is escalated to directly, prompted to act
4. **Always** — Full audit trail via SharePoint version history: who was assigned, when, any reassignments, and when status changed

---

## Rotation Queue: List Schema

| Field | Type | Purpose |
|---|---|---|
| Last Name | Text | Identification / sorting |
| First Name | Text | Identification |
| Email Address | Text (Email) | Where assignment notifications are sent |
| Active | Yes/No | Whether this person is currently in the rotation pool at all |
| Unavailable Start Date | Date | Start of a planned absence (vacation, leave) |
| Unavailable End Date | Date | End of a planned absence — person auto-returns to rotation the day after |
| Rotation Order | Number | Position in the round-robin sequence |
| Last Assigned Date | Date | Set automatically when this person receives a review; used to determine "next up" |

**Logic notes:**
- **Decision: "Next up" is determined by Last Assigned Date** — the active person (not currently within an unavailable date range) with the oldest Last Assigned Date gets the next review. This self-corrects automatically if the list changes (new hires, departures, overrides) without needing to renumber anything.
- Deactivating someone (Active = No) removes them from consideration entirely, distinct from a temporary unavailable date range
- Manual overrides by the National Manager don't update Last Assigned Date for the *original* auto-assigned person — only for whoever ends up actually assigned — so the rotation stays fair
- Rotation Order field can be dropped from the schema below since Last Assigned Date now drives the logic — kept here only if you want a simple visual ordering for reference

---

## Review Inventory (Tracking List): Schema

| Field | Type | Purpose |
|---|---|---|
| Archer Model Number | Text | Identifies which model this review covers — parsed from the Archer email |
| Assigned Data Scientist (Last, First) | Text / Lookup | Who's doing the review |
| Data Scientist Email | Text (Email) | For notifications tied to this specific review |
| Start Date | Date | When the review was assigned/opened — parsed from the Archer email or set to assignment date |
| Due Date | Date | Deadline — parsed from the Archer email |
| Status | Choice (Not Started / In Progress / Complete) | Updated by the DS as work progresses |
| Completion Date | Date | Set automatically when Status is changed to Complete |
| Time to Completion | Calculated (Completion Date − Start Date) | Auto-calculated once Completion Date is populated; basis for tracking turnaround performance |
| Assigned By | Choice (Auto / Manager Override) | Distinguishes automatic round-robin assignments from manual overrides, for audit purposes |

**Why Time to Completion matters beyond this workflow:** once you're tracking Start Date, Due Date, and Completion Date consistently across every review, this becomes a reportable metric — average turnaround time, on-time completion rate, workload distribution across DS — which is exactly the kind of evidence that supports the case for you owning this process going forward.

---

## Spreadsheet Sync Behavior

The two shared spreadsheets are **not** live-linked to Snowflake — this is a one-way, scheduled sync, not real-time:

- **Spreadsheet → Snowflake:** real. The automation reads current spreadsheet contents on every scheduled run and acts on them (assigns based on current Rotation Queue, updates Snowflake based on current Status column). Lag = time between runs, not instant.
- **Snowflake → Spreadsheet:** does not happen. The script only ever reads the spreadsheets, never writes to them — a manager's or DS's entry is never silently overwritten or "corrected."
- **Rotation Queue ↔ Review Status spreadsheet:** fully independent of each other.
- **Safeguard needed:** the sync logic must act on a status *change*, not a status *value* — otherwise a review sitting at "Complete" would re-trigger the closure notification on every run. Minor build detail, but a real one.

**File location: network share on/near the Python server.** Both spreadsheets live in a shared network folder attached to the same server the automation runs on (e.g. a mapped drive, like `\\servername\modelmonitoring\`). Managers and the DS open/edit them like any normal network file; the script reads them directly off the filesystem — no cloud sync, no API call, no sync-delay uncertainty beyond the scheduled run itself. TFS already has shared network drives in place, so this requires no new infrastructure request.

**Concurrent-edit risk:** acceptable as-is, since simultaneous edits by two people are unlikely given team size and usage pattern. Worth revisiting only if that assumption changes.

---

## Open Items for Next Phase (Data Pieces)

- Confirm exact fields/format in the Archer-generated email for parsing
- Confirm the specific network share/folder path for the two spreadsheets, and who has write access
- Confirm scheduling mechanism on the Python server (cron or equivalent) and run frequency
- Confirm Microsoft Graph API access/app registration for reading the shared mailbox — needs IT
- Decide whether Governance should receive an automated closure notification, or if that stays with the National Manager
