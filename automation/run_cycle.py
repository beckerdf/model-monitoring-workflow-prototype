"""
Entry point for one full automation cycle. This is what the Python server's
scheduler (cron or equivalent) calls on the configured interval.

Each step is intentionally isolated with its own try/except so a failure in
one part (e.g. mailbox unreachable) doesn't block the others (e.g. reminders
still get checked) -- the review process shouldn't have a single point of
failure the way the manual version did.
"""
import logging
from datetime import date

from . import config, email_parser, file_mailbox as graph_mailbox, file_notifications as notifications, reminders, review_inventory, rotation_queue, status_sync

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("model_monitoring_workflow")


def process_new_governance_emails() -> None:
    try:
        bodies = graph_mailbox.fetch_new_governance_emails(config.RUN_INTERVAL_MINUTES)
    except Exception:
        log.exception("Could not fetch governance emails this cycle")
        return

    if not bodies:
        log.info("No new governance emails.")
        return

    people = rotation_queue.load_rotation_queue(config.ROTATION_QUEUE_PATH)

    for body in bodies:
        try:
            parsed = email_parser.parse_email_body(body)
        except ValueError:
            log.exception("Could not parse a governance email -- skipping, needs manual review")
            continue

        assignee = rotation_queue.next_assignee(people, as_of=date.today())
        if assignee is None:
            log.warning(
                f"No eligible data scientist available for {parsed.model_name}. "
                f"Manager should be alerted manually -- rotation queue may be empty or fully unavailable."
            )
            continue

        review_id = review_inventory.create_review(
            model_name=parsed.model_name,
            assigned_ds_email=assignee.email,
            assigned_ds_name=assignee.full_name,
            start_date=parsed.start_date,
            due_date=parsed.due_date,
        )
        notifications.notify_assignment(
            assignee.email, assignee.full_name, parsed.model_name, parsed.due_date
        )
        log.info(f"Assigned {parsed.model_name} ({review_id}) to {assignee.full_name}")

        # reflect the new assignment in-memory so the next email in this same
        # batch doesn't pick the same person again before the spreadsheet catches up
        assignee.last_assigned = date.today()


def sync_ds_status_updates() -> None:
    try:
        changes = status_sync.sync_status_changes(config.REVIEW_STATUS_PATH)
    except Exception:
        log.exception("Could not sync review status updates this cycle")
        return

    for review_id, old_status, new_status in changes:
        log.info(f"Status changed for {review_id}: {old_status} -> {new_status}")
        if new_status == "Complete":
            open_reviews = {r.review_id: r for r in review_inventory.get_open_reviews()}
            review = open_reviews.get(review_id)
            if review:
                notifications.notify_closure(review.model_name, review.assigned_ds_name)


def run_reminders() -> None:
    try:
        reminders.check_reminders_and_escalations()
    except Exception:
        log.exception("Could not run reminder/escalation check this cycle")


def run_cycle() -> None:
    log.info("Starting automation cycle")
    process_new_governance_emails()
    sync_ds_status_updates()
    run_reminders()
    log.info("Cycle complete")


if __name__ == "__main__":
    run_cycle()
