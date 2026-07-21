"""
Manual end-to-end test: runs a REAL governance email through the parser,
picks a real assignee from a test Rotation Queue, and writes a real row
into Snowflake -- all without needing live mailbox reading wired up yet.

Run this from the PARENT directory (prototype_model_monitoring), as a module:
    python -m automation.manual_e2e_test

(Not `python manual_e2e_test.py` directly from inside automation/ -- this
module relies on package-relative imports the same way run_cycle.py does,
so it needs to run the same way.)

Requires:
- test_rotation_queue.xlsx in the automation/ directory (already created)
- Snowflake connection details set as environment variables, or edit
  config.py defaults directly for this one-off test
"""
from datetime import date
from pathlib import Path

from .email_parser import parse_email_body
from .rotation_queue import load_rotation_queue, next_assignee
from .review_inventory import create_review, get_open_reviews

TEST_QUEUE_PATH = Path(__file__).parent / "test_rotation_queue.xlsx"

# Paste the real email body here (or read from a .txt file if you'd rather)
REAL_EMAIL_BODY = """
Hello,

You are receiving this notification as the model monitoring process is scheduled to start on: 7/6/2026

Model Record Name: Service Ops Credit Loss

No action is required at this time, however, please plan on beginning the monitoring as scheduled.
"""

print("=" * 60)
print("STEP 1: Parsing the email")
print("=" * 60)
parsed = parse_email_body(REAL_EMAIL_BODY)
print(f"Model Name : {parsed.model_name}")
print(f"Start Date : {parsed.start_date}")
print(f"Due Date   : {parsed.due_date}  (assumes 49-day cycle -- confirm this)")

print()
print("=" * 60)
print("STEP 2: Loading the Rotation Queue and picking an assignee")
print("=" * 60)
people = load_rotation_queue(TEST_QUEUE_PATH)
print(f"Loaded {len(people)} people from the test queue:")
for p in people:
    print(f"  - {p.full_name} | active={p.active} | last_assigned={p.last_assigned}")

assignee = next_assignee(people, as_of=date.today())
if assignee is None:
    print("\nNo eligible assignee found -- check the test spreadsheet.")
    raise SystemExit(1)
print(f"\n>>> Assigned to: {assignee.full_name} ({assignee.email})")

print()
print("=" * 60)
print("STEP 3: Writing the review to Snowflake")
print("=" * 60)
print("(This will prompt for SSO login in a browser if this is a new session)")
review_id = create_review(
    model_name=parsed.model_name,
    assigned_ds_email=assignee.email,
    assigned_ds_name=assignee.full_name,
    start_date=parsed.start_date,
    due_date=parsed.due_date,
)
print(f"Created review: {review_id}")

print()
print("=" * 60)
print("STEP 4: Confirming it's actually there")
print("=" * 60)
open_reviews = get_open_reviews()
match = [r for r in open_reviews if r.review_id == review_id]
if match:
    r = match[0]
    print("Confirmed in Snowflake:")
    print(f"  Model     : {r.model_name}")
    print(f"  Assigned  : {r.assigned_ds_name} <{r.assigned_ds_email}>")
    print(f"  Start/Due : {r.start_date} / {r.due_date}")
    print(f"  Status    : {r.status}")
    print(f"  Assigned By: {r.assigned_by}")
else:
    print("WARNING: review was created but not found in get_open_reviews() -- investigate.")

print()
print("END-TO-END TEST COMPLETE")
