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
- **Automation Layer** (Power Automate) — parses, assigns, tracks, notifies
- **System of Record** (SharePoint list) — rotation queue, review inventory, status, audit trail
- **National Manager** — owns keeping the Rotation Queue accurate (active/inactive, unavailable date ranges); otherwise passive by default, active only for per-review overrides and overdue escalations
- **Data Scientist** — receives assignment, performs review in Archer, updates status

### National Manager Responsibility: Rotation Queue Maintenance
The automation is only as accurate as the pool it's assigning from. National Managers are responsible for keeping the Rotation Queue current, on an ongoing basis:
- **Add** a Data Scientist when onboarded/ready to take reviews
- **Deactivate** a Data Scientist who leaves the team or role
- **Set unavailable dates** for planned absences (e.g., vacation) — manager enters a start and end date directly on the DS's row; the assignment logic checks these dates automatically and skips that person for any review triggered within that window, no manual toggle needed before or after
This is a direct edit to the SharePoint list — no approval step or flow needed. Because assignment logic reads the list live each time a review comes in, any update a manager makes — including unavailable dates — is reflected on the very next assignment automatically, and the person returns to rotation on their own the day after the end date with no manager action required.

### Step-by-Step Flow

1. **Trigger** — Governance sends the standardized Archer-generated email to a shared/dedicated inbox
2. **Parse** — Power Automate flow reads the consistent email format and extracts: model name, review ID, due date
3. **Assign** — Flow checks the SharePoint Rotation Queue for the next Data Scientist in line (round-robin), skipping anyone whose unavailable date range covers the current date (e.g., PTO)
4. **Log** — Flow creates a new record in the SharePoint "Model Monitoring Reviews" list: model, assigned DS, due date, status = *Not Started*, date assigned
5. **Notify** — Flow auto-emails the assigned DS with review details and due date; CCs the National Manager and DB for visibility
6. **(Optional) Override** — National Manager can reassign directly in the SharePoint list at any time (e.g., DS is on vacation); this triggers a reassignment notification and keeps the rotation queue consistent
7. **Work performed** — DS completes the model monitoring review in Archer, then updates status in the SharePoint list (Not Started → In Progress → Complete)
8. **Automated reminders** — Scheduled flow checks open items daily:
   - 7 days before due: reminder to DS
   - 2 days before due: reminder to DS, CC National Manager and DB
   - Past due: escalation email to National Manager and DB, flagged overdue
9. **Closure loop** — When marked Complete, flow optionally notifies Governance (or National Manager and DB) that the review is done, closing the loop that's currently missing
10. **Reporting/visibility** — Filtered SharePoint view (or Power BI tile) gives National Managers a live, one-glance dashboard: upcoming due dates, overdue items, workload by DS

---

## System of Record: What Lives Where

| Component | Tool | Purpose |
|---|---|---|
| Rotation Queue | SharePoint list | Ordered list of DS names, "next up" pointer, availability flag |
| Review Inventory | SharePoint list | One row per review: model, DS, due date, status, dates |
| Automation logic | Power Automate | Parse email, assign, notify, remind, escalate |
| Process documentation | Confluence | Runbook / reference doc for how the workflow operates (org standard) |
| Reporting view | SharePoint filtered view or Power BI | Live overdue/upcoming dashboard for managers |

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

## Open Items for Next Phase (Data Pieces)

- Confirm exact fields/format in the Archer-generated email for parsing
- Define the Rotation Queue starting order and availability-flag process (who updates it, how often)
- Decide DS Complete-confirmation format — SharePoint list edit vs. simple Power Automate form
- Decide whether Governance should receive an automated closure notification, or if that stays with the National Manager
