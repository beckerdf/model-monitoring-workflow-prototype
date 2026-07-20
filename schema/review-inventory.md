# Review Inventory — Schema

One row per model monitoring review. This is the tracking mechanism that doesn't
exist in the current process.

| Field | Type | Notes |
|---|---|---|
| Archer Model Number | Text | Parsed from the Archer-generated governance email |
| Assigned Data Scientist (Last, First) | Text / Lookup | |
| Data Scientist Email | Text (Email) | |
| Start Date | Date | Parsed from the governance email |
| Due Date | Date | Parsed from the governance email |
| Status | Choice | Not Started / In Progress / Complete |
| Completion Date | Date | Set automatically when Status → Complete |
| Time to Completion | Calculated | Completion Date − Start Date |
| Assigned By | Choice | Auto / Manager Override |

## Reminder cadence

- **7 days before due:** reminder to the DS
- **2 days before due:** reminder to the DS, CC National Manager and DB
- **Past due, not Complete:** escalation to National Manager and DB, flagged overdue

## Open — data capture & flow (to be detailed as the repo is built out)

- Exact field mapping from the Archer-generated email (subject line / body format)
- Whether Start Date is parsed from the email or set to assignment date
- How Completion is confirmed by the DS (list edit vs. simple form)
- Whether Governance receives an automated closure notification
