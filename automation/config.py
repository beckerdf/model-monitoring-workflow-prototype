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
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "MODEL_GOVERNANCE")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA", "MONITORING_WORKFLOW")

REVIEW_INVENTORY_TABLE = f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.REVIEW_INVENTORY"

# --- Mailbox (Microsoft Graph API) ---
GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "")
GOVERNANCE_MAILBOX = os.environ.get("GOVERNANCE_MAILBOX", "modelgovernance@tfs.com")

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
