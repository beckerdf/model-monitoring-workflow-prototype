"""
File-based notifications: instead of calling Graph API to send mail,
writes a small plain-text file per notification into bridge/outbound/. A
second Outlook VBA routine on DB's Windows laptop polls this folder (after
a git pull), sends each one through Outlook, deletes the file, and pushes
the deletion back.

Plain delimited text rather than JSON deliberately -- VBA has no built-in
JSON support, and this format parses with nothing but Split() and
Line Input, so the Outlook side needs no extra library setup.

File format:
    TO: addr1;addr2
    CC: addr1;addr2
    SUBJECT: ...
    BODY_START
    (body text, may span multiple lines)
    BODY_END

Same function signatures as the old notifications.py so run_cycle.py and
reminders.py don't need to change at all -- only the import at the top.
"""
import os
import uuid

from . import config


def _write_notification(to: list[str], cc: list[str], subject: str, body: str) -> None:
    os.makedirs(config.BRIDGE_OUTBOUND_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}.txt"
    filepath = os.path.join(config.BRIDGE_OUTBOUND_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"TO: {';'.join(to)}\n")
        f.write(f"CC: {';'.join(cc)}\n")
        f.write(f"SUBJECT: {subject}\n")
        f.write("BODY_START\n")
        f.write(body)
        f.write("\nBODY_END\n")


def notify_assignment(ds_email: str, ds_name: str, model_name: str, due_date) -> None:
    cc = config.NATIONAL_MANAGER_EMAILS + ([config.DB_EMAIL] if config.DB_EMAIL else [])
    _write_notification(
        to=[ds_email],
        cc=cc,
        subject=f"Model Monitoring Review Assigned: {model_name}",
        body=(
            f"Hi {ds_name},\n\n"
            f"You've been assigned the model monitoring review for {model_name}.\n"
            f"Due date: {due_date}\n\n"
            f"This was assigned automatically based on the current rotation queue."
        ),
    )


def notify_reminder(ds_email: str, ds_name: str, model_name: str, due_date, cc_manager: bool) -> None:
    cc = (config.NATIONAL_MANAGER_EMAILS + ([config.DB_EMAIL] if config.DB_EMAIL else [])) if cc_manager else []
    _write_notification(
        to=[ds_email],
        cc=cc,
        subject=f"Reminder: {model_name} due {due_date}",
        body=f"Hi {ds_name},\n\nThis is a reminder that {model_name} is due {due_date}.",
    )


def notify_overdue_escalation(model_name: str, ds_name: str, due_date) -> None:
    cc = config.NATIONAL_MANAGER_EMAILS + ([config.DB_EMAIL] if config.DB_EMAIL else [])
    _write_notification(
        to=cc,
        cc=[],
        subject=f"OVERDUE: {model_name} (assigned to {ds_name})",
        body=(
            f"{model_name} was due {due_date} and is not yet marked Complete.\n"
            f"Assigned to: {ds_name}"
        ),
    )


def notify_closure(model_name: str, ds_name: str) -> None:
    cc = config.NATIONAL_MANAGER_EMAILS + ([config.DB_EMAIL] if config.DB_EMAIL else [])
    _write_notification(
        to=cc,
        cc=[],
        subject=f"Completed: {model_name}",
        body=f"{model_name} was marked Complete by {ds_name}.",
    )
