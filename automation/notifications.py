"""
Notifications: assignment, reminder, and escalation emails.

Uses the same Graph API app registration as graph_mailbox.py to send mail
as the governance/automation account. Blocked on the same IT dependency.
"""
import requests

from . import config
from .graph_mailbox import _get_access_token, GRAPH_BASE_URL


def _send_mail(to: list[str], cc: list[str], subject: str, body: str) -> None:
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    message = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": a}} for a in to],
            "ccRecipients": [{"emailAddress": {"address": a}} for a in cc],
        }
    }
    url = f"{GRAPH_BASE_URL}/users/{config.GOVERNANCE_MAILBOX}/sendMail"
    resp = requests.post(url, headers=headers, json=message)
    resp.raise_for_status()


def notify_assignment(ds_email: str, ds_name: str, model_name: str, due_date) -> None:
    cc = config.NATIONAL_MANAGER_EMAILS + ([config.DB_EMAIL] if config.DB_EMAIL else [])
    _send_mail(
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
    _send_mail(
        to=[ds_email],
        cc=cc,
        subject=f"Reminder: {model_name} due {due_date}",
        body=f"Hi {ds_name},\n\nThis is a reminder that {model_name} is due {due_date}.",
    )


def notify_overdue_escalation(model_name: str, ds_name: str, due_date) -> None:
    cc = config.NATIONAL_MANAGER_EMAILS + ([config.DB_EMAIL] if config.DB_EMAIL else [])
    _send_mail(
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
    _send_mail(
        to=cc,
        cc=[],
        subject=f"Completed: {model_name}",
        body=f"{model_name} was marked Complete by {ds_name}.",
    )
