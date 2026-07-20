"""
Mailbox access via Microsoft Graph API.

*** BLOCKED ON IT: requires an app registration in Azure AD with
    Mail.Read (application) permission granted for the governance
    shared mailbox. Nothing in this module can be tested end-to-end
    until that's in place. ***

Structure is ready to fill in once credentials exist -- the rest of the
codebase only depends on fetch_new_governance_emails() returning a list
of plain-text email bodies, so swapping the real Graph calls in here is
isolated to this file.
"""
import requests

from . import config

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


def _get_access_token() -> str:
    """Client-credentials OAuth flow against Azure AD."""
    token_url = f"https://login.microsoftonline.com/{config.GRAPH_TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(token_url, data={
        "client_id": config.GRAPH_CLIENT_ID,
        "client_secret": config.GRAPH_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_new_governance_emails(since_minutes: int) -> list[str]:
    """
    Returns plain-text bodies of unread governance emails received in the
    last `since_minutes`. Does not mark them as read here -- that should
    happen only after successful parsing + assignment, so a crash mid-run
    doesn't silently drop an email.
    """
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = (
        f"{GRAPH_BASE_URL}/users/{config.GOVERNANCE_MAILBOX}/mailFolders/inbox/messages"
        f"?$filter=isRead eq false&$select=id,body"
    )
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    messages = resp.json().get("value", [])
    return [m["body"]["content"] for m in messages]


def mark_as_read(message_id: str) -> None:
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE_URL}/users/{config.GOVERNANCE_MAILBOX}/messages/{message_id}"
    requests.patch(url, headers=headers, json={"isRead": True})
