"""
National manager walkthrough: demonstrates the full review lifecycle against
the real Snowflake tables -- multiple assignments rotating fairly, a manager
override, a DS status update flowing through, and the reminder/escalation
logic actually firing.

Run from the parent directory (prototype_model_monitoring):
    python -m automation.walkthrough_demo

Uses demo_rotation_queue.xlsx and demo_review_status.xlsx (in automation/)
rather than the single-purpose test files from the earlier smoke test, so
this can be re-run cleanly for a live audience without interference.
"""
from datetime import date, timedelta
from pathlib import Path

from .email_parser import ParsedReview
from .rotation_queue import load_rotation_queue, next_assignee
from .review_inventory import create_review, get_open_reviews, reassign
from .status_sync import sync_status_changes
from .reminders import check_reminders_and_escalations

QUEUE_PATH = Path(__file__).parent / "demo_rotation_queue.xlsx"
STATUS_PATH = Path(__file__).parent / "demo_review_status.xlsx"

TODAY = date.today()

# Three realistic "incoming governance emails" -- staggered due dates so the
# reminder/escalation demo has something to actually fire on.
DEMO_EMAILS = [
    ParsedReview(model_name="Service Ops Credit Loss", start_date=TODAY - timedelta(days=45), due_date=TODAY + timedelta(days=4)),   # due soon
    ParsedReview(model_name="Return Rate Model 2.1 - MFS", start_date=TODAY - timedelta(days=60), due_date=TODAY - timedelta(days=2)),  # overdue
    ParsedReview(model_name="Recovery Income", start_date=TODAY - timedelta(days=10), due_date=TODAY + timedelta(days=39)),           # not urgent
]


def pause(label: str):
    print(f"\n--- {label} ---")
    input("(press Enter to continue) ")


def header(title: str):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def main():
    header("1. AUTO-ASSIGNMENT: three governance emails, processed in order")
    people = load_rotation_queue(QUEUE_PATH)
    print("Rotation Queue loaded:")
    for p in people:
        flag = " (on vacation)" if p.is_unavailable_on(TODAY) else ""
        print(f"  - {p.full_name:20s} last assigned {p.last_assigned}{flag}")

    created_ids = []
    for email in DEMO_EMAILS:
        assignee = next_assignee(people, as_of=TODAY)
        review_id = create_review(
            model_name=email.model_name,
            assigned_ds_email=assignee.email,
            assigned_ds_name=assignee.full_name,
            start_date=email.start_date,
            due_date=email.due_date,
        )
        created_ids.append((review_id, email.model_name))
        assignee.last_assigned = TODAY  # reflect in-memory so the next pick rotates fairly
        print(f"  '{email.model_name}' -> {assignee.full_name}  (due {email.due_date})")

    pause("Notice: each review went to a different person, oldest-last-assigned first")

    header("2. MANAGER OVERRIDE: reassigning one review by hand")
    override_id, override_model = created_ids[0]
    new_person = people[2]  # Rohan -- normally on vacation, manager overriding anyway
    print(f"Reassigning '{override_model}' to {new_person.full_name} (manager override)")
    reassign(override_id, new_person.email, new_person.full_name)
    print("Done -- Assigned By now shows 'Manager Override' for this review")

    pause("This is the entire override workflow: one function call, fully logged")

    header("3. DATA SCIENTIST STATUS UPDATE: via the shared spreadsheet")
    complete_id, complete_model = created_ids[2]
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Review ID", "Status"])
    ws.append([complete_id, "Complete"])
    wb.save(STATUS_PATH)
    print(f"DS marked '{complete_model}' Complete in the spreadsheet")

    changes = sync_status_changes(STATUS_PATH)
    for review_id, old, new in changes:
        print(f"  Synced to Snowflake: {review_id} : {old} -> {new}")

    pause("No app, no login -- just an Excel edit, picked up automatically")

    header("4. REMINDERS & ESCALATION: checking due dates against today")
    check_reminders_and_escalations(today=TODAY)
    print("(Reminder/escalation emails would send here once mailbox access is live --")
    print(" for today's demo, check the Snowflake REMINDER_*_SENT_AT / OVERDUE_ESCALATED_AT")
    print(" columns to see which reviews got flagged.)")

    pause("The overdue review and the due-soon review should both be flagged now")

    header("5. CURRENT STATE: what a national manager would actually see")
    open_reviews = get_open_reviews()
    print(f"{'Model':30s} {'Assigned To':20s} {'Due':12s} {'Status'}")
    print("-" * 80)
    for r in open_reviews:
        print(f"{r.model_name:30s} {r.assigned_ds_name:20s} {str(r.due_date):12s} {r.status}")

    print("\nWALKTHROUGH COMPLETE")


if __name__ == "__main__":
    main()
