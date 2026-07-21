"""
Central configuration for the model monitoring assignment automation.

All values are read from environment variables so nothing sensitive
(paths, credentials) lives in source control. Copy .env.example to .env
and fill in real values, or set these as real environment variables on
the Python server.
"""
import os
from pathlib import Path

# --- File locations (network share on/near the Python server) ---
ROTATION_QUEUE_PATH = Path(os.environ.get(
    "ROTATION_QUEUE_PATH", r"\\servername\modelmonitoring\rotation_queue.xlsx"
))
REVIEW_STATUS_PATH = Path(os.environ.get(
    "REVIEW_STATUS_PATH", r"\\servername\modelmonitoring\review_status.xlsx"
))

# --- Snowflake connection (system of record) ---
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER", "")
# SSO by default (DB logs in via SSO) -- no password needed/stored.
# Set SNOWFLAKE_AUTHENTICATOR=password and SNOWFLAKE_PASSWORD if a service
# account with password auth is used later (e.g. for the unattended
# scheduled job, since SSO needs an interactive browser login).
SNOWFLAKE_AUTHENTICATOR = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "externalbrowser")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "EDP_PRD_WSP")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA", "VPP_ANALYTICS")

REVIEW_INVENTORY_TABLE = f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.REVIEW_INVENTORY"

# --- Mailbox (Microsoft Graph API) ---
# Interim setup: monitoring DB's own TFS mailbox rather than a dedicated
# shared governance mailbox, to avoid requesting a new mailbox + app-only
# permissions from IT. This uses DELEGATED auth (DB signs in once, acting
# as himself) rather than application permissions (which would need admin
# approval to read/send from any mailbox in the tenant). Revisit once/if
# a real shared mailbox is set up -- at that point this reverts to the
# app-only pattern originally scoped.
GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
MONITORED_MAILBOX = os.environ.get("MONITORED_MAILBOX", "")  # DB's own TFS email address
GOVERNANCE_SENDER_FILTER = os.environ.get(
    "GOVERNANCE_SENDER_FILTER", ""
)  # governance's from-address, so we only pick up their emails, not everything in the inbox

# --- Notification routing ---
NATIONAL_MANAGER_EMAILS = [
    e.strip() for e in os.environ.get("NATIONAL_MANAGER_EMAILS", "").split(",") if e.strip()
]
DB_EMAIL = os.environ.get("DB_EMAIL", "")

# --- Reminder cadence (days before/after due date) ---
REMINDER_DAYS_BEFORE_DUE = [7, 2]
ESCALATE_WHEN_OVERDUE = True

# --- Run cadence ---
RUN_INTERVAL_MINUTES = int(os.environ.get("RUN_INTERVAL_MINUTES", "30"))
