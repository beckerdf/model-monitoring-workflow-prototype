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
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "toyotafinancialservices_tfsprod.us-east-1.privatelink")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER", "")
SNOWFLAKE_ROLE = os.environ.get("SNOWFLAKE_ROLE", "EDP_PRD_WSP_VPP_ANALYTICS_SUPPORT")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "WSP_WH")
SNOWFLAKE_AUTHENTICATOR = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "https://tfs.okta.com/")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "EDP_PRD_WSP")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA", "VPP_ANALYTICS")

REVIEW_INVENTORY_TABLE = f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.REVIEW_INVENTORY"

# --- Mailbox (Microsoft Graph API) ---
GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
MONITORED_MAILBOX = os.environ.get("MONITORED_MAILBOX", "")
GOVERNANCE_SENDER_FILTER = os.environ.get("GOVERNANCE_SENDER_FILTER", "")

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
