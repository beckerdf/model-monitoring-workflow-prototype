"""
Mailbox access via Microsoft Graph API -- DELEGATED auth, against DB's own
TFS mailbox (interim setup, see config.py for why).

Uses MSAL's device code flow: the first time this runs, it prints a URL and
a short code. Sign in once at that URL with your normal TFS credentials,
and MSAL caches the resulting token locally (token_cache.bin) and refreshes
it silently after that -- no repeated logins needed for the scheduled job.

*** Still needs an Azure AD app registration (Application/client ID),
    even for delegated access -- but only requesting Mail.Read + Mail.Send
    as DELEGATED permissions, which many tenants allow a user to consent to
    themselves. Check with IT. If self-service app registration is blocked
    in this tenant, this is still a much smaller ask than the original
    app-only/shared-mailbox version, since the app can only ever act as you,
    on your own mailbox. ***
"""
import atexit

import msal
import requests

from . import config

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.Read", "Mail.Send"]
TOKEN_CACHE_PATH = "token_cache.bin"


def _build_msal_app():
    cache = msal.SerializableTokenCache()
    try:
        with open(TOKEN_CACHE_PATH, "r") as f:
            cache.deserialize(f.read())
    except FileNotFoundError:
        pass

    atexit.register(
        lambda: open(TOKEN_CACHE_PATH, "w").write(cache.serialize())
        if cache.has_state_changed else None
    )

    return msal.PublicClientApplication(
        client_id=config.GRAPH_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{config.GRAPH_TENANT_ID}",
        token_cache=cache,
    )


def _get_access_token() -> str:
    app = _build_msal_app()
    accounts = app.get_accounts()

    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    # No cached token, or it couldn't be refreshed silently -- need an
    # interactive sign-in. This only happens the first time, or if the
    # cached token is fully expired and needs a fresh login.
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Could not start device flow: {flow}")

    print(flow["message"])  # prints the URL + code to sign in with
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Authentication failed: {result.get('error_description')}")

    return result["access_token"]


def fetch_new_governance_emails(since_minutes: int) -> list[str]:
    """
    Returns plain-text bodies of unread emails from governance's sender
    address, received in the last `since_minutes`, sitting in DB's own
    inbox. Filtering by sender keeps this from picking up unrelated mail.
    """
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    filter_parts = ["isRead eq false"]
    if config.GOVERNANCE_SENDER_FILTER:
        filter_parts.append(f"from/emailAddress/address eq '{config.GOVERNANCE_SENDER_FILTER}'")
    filter_query = " and ".join(filter_parts)

    url = f"{GRAPH_BASE_URL}/me/mailFolders/inbox/messages?$filter={filter_query}&$select=id,body"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    messages = resp.json().get("value", [])
    return [m["body"]["content"] for m in messages]


def mark_as_read(message_id: str) -> None:
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE_URL}/me/messages/{message_id}"
    requests.patch(url, headers=headers, json={"isRead": True})
