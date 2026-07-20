# Rotation Queue — Schema

Source of truth for which data scientists are eligible to receive the next model
monitoring review, and in what order.

| Field | Type | Notes |
|---|---|---|
| Last Name | Text | |
| First Name | Text | |
| Email Address | Text (Email) | Notification target |
| Active | Yes/No | Removes from consideration entirely when No |
| Unavailable Start Date | Date | Start of a planned absence |
| Unavailable End Date | Date | Person auto-returns to rotation the day after |
| Last Assigned Date | Date | Set automatically on assignment; drives "next up" |

## Assignment logic

"Next up" = the **Active** person, not currently within an unavailable date range,
with the **oldest Last Assigned Date**. This self-corrects automatically as people
are added, removed, or reassigned — no manual renumbering required.

Manager overrides update Last Assigned Date only for whoever ends up actually
assigned, not the original auto-picked person, so the rotation stays fair.

## Maintenance ownership

National Managers own keeping this list current:
- Add a DS when onboarded and ready to take reviews
- Deactivate a DS who leaves the team or role
- Set unavailable date ranges for planned absences

This is a direct edit — no approval workflow needed. Assignment logic reads the
list live on every incoming review, so changes take effect immediately.
