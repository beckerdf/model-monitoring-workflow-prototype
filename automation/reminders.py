"""
Reminder & escalation logic: checks every open review's due date against
today, and fires the appropriate notification -- but only once per
threshold, using the *_SENT_AT columns as a guard against re-sending on
every run.
"""
from datetime import date

from . import review_inventory, file_notifications as notifications, config


def check_reminders_and_escalations(today: date | None = None) -> None:
    today = today or date.today()
    open_reviews = review_inventory.get_open_reviews()

    for review in open_reviews:
        days_until_due = (review.due_date - today).days

        if days_until_due < 0 and config.ESCALATE_WHEN_OVERDUE:
            notifications.notify_overdue_escalation(
                review.model_name, review.assigned_ds_name, review.due_date
            )
            review_inventory.mark_reminder_sent(review.review_id, "overdue")

        elif days_until_due == 2:
            notifications.notify_reminder(
                review.assigned_ds_email, review.assigned_ds_name,
                review.model_name, review.due_date, cc_manager=True,
            )
            review_inventory.mark_reminder_sent(review.review_id, "2day")

        elif days_until_due == 7:
            notifications.notify_reminder(
                review.assigned_ds_email, review.assigned_ds_name,
                review.model_name, review.due_date, cc_manager=False,
            )
            review_inventory.mark_reminder_sent(review.review_id, "7day")
