"""
Review Inventory: Snowflake is the single system of record for every review.
This module is the only thing in the codebase that reads from or writes to it.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from . import config


@dataclass
class Review:
    review_id: str
    model_name: str
    archer_model_number: Optional[str]
    assigned_ds_email: str
    assigned_ds_name: str
    start_date: date
    due_date: date
    status: str
    completion_date: Optional[date]
    assigned_by: str


@contextmanager
def get_connection():
    import snowflake.connector  # imported lazily so this module loads fine even before the package is installed

    connect_kwargs = dict(
        account=config.SNOWFLAKE_ACCOUNT,
        user=config.SNOWFLAKE_USER,
        warehouse=config.SNOWFLAKE_WAREHOUSE,
        database=config.SNOWFLAKE_DATABASE,
        schema=config.SNOWFLAKE_SCHEMA,
    )
    if config.SNOWFLAKE_AUTHENTICATOR == "externalbrowser":
        # SSO: opens a browser window for login the first time in a session;
        # no password needed or stored.
        connect_kwargs["authenticator"] = "externalbrowser"
    else:
        connect_kwargs["password"] = config.SNOWFLAKE_PASSWORD

    conn = snowflake.connector.connect(**connect_kwargs)
    try:
        yield conn
    finally:
        conn.close()


def _log_event(cursor, review_id: str, event_type: str, detail: str = "") -> None:
    cursor.execute(
        f"""INSERT INTO {config.SNOWFLAKE_DATABASE}.{config.SNOWFLAKE_SCHEMA}.REVIEW_INVENTORY_AUDIT_LOG
            (REVIEW_ID, EVENT_TYPE, DETAIL) VALUES (%s, %s, %s)""",
        (review_id, event_type, detail),
    )


def create_review(
    model_name: str,
    assigned_ds_email: str,
    assigned_ds_name: str,
    start_date: date,
    due_date: date,
    archer_model_number: Optional[str] = None,
    assigned_by: str = "Auto",
) -> str:
    """Insert a new review, auto-assigned by the rotation logic. Returns the new REVIEW_ID."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""INSERT INTO {config.REVIEW_INVENTORY_TABLE}
                (MODEL_NAME, ARCHER_MODEL_NUMBER, ASSIGNED_DS_EMAIL, ASSIGNED_DS_NAME,
                 START_DATE, DUE_DATE, STATUS, ASSIGNED_BY)
                VALUES (%s, %s, %s, %s, %s, %s, 'Not Started', %s)""",
            (model_name, archer_model_number, assigned_ds_email, assigned_ds_name,
             start_date, due_date, assigned_by),
        )
        cur.execute(
            f"""SELECT REVIEW_ID FROM {config.REVIEW_INVENTORY_TABLE}
                WHERE MODEL_NAME = %s ORDER BY CREATED_AT DESC LIMIT 1""",
            (model_name,),
        )
        review_id = cur.fetchone()[0]
        _log_event(cur, review_id, "assigned", f"Auto-assigned to {assigned_ds_name}")
        conn.commit()
        return review_id


def get_open_reviews() -> list[Review]:
    """All reviews not yet Complete — used for reminder/escalation checks."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""SELECT REVIEW_ID, MODEL_NAME, ARCHER_MODEL_NUMBER, ASSIGNED_DS_EMAIL,
                       ASSIGNED_DS_NAME, START_DATE, DUE_DATE, STATUS, COMPLETION_DATE, ASSIGNED_BY
                FROM {config.REVIEW_INVENTORY_TABLE}
                WHERE STATUS != 'Complete'"""
        )
        return [Review(*row) for row in cur.fetchall()]


def update_status(review_id: str, new_status: str) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        completion_date = "CURRENT_DATE()" if new_status == "Complete" else "NULL"
        cur.execute(
            f"""UPDATE {config.REVIEW_INVENTORY_TABLE}
                SET STATUS = %s, COMPLETION_DATE = {completion_date}, UPDATED_AT = CURRENT_TIMESTAMP()
                WHERE REVIEW_ID = %s""",
            (new_status, review_id),
        )
        _log_event(cur, review_id, "status_changed", f"Status -> {new_status}")
        conn.commit()


def reassign(review_id: str, new_ds_email: str, new_ds_name: str) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""UPDATE {config.REVIEW_INVENTORY_TABLE}
                SET ASSIGNED_DS_EMAIL = %s, ASSIGNED_DS_NAME = %s,
                    ASSIGNED_BY = 'Manager Override', UPDATED_AT = CURRENT_TIMESTAMP()
                WHERE REVIEW_ID = %s""",
            (new_ds_email, new_ds_name, review_id),
        )
        _log_event(cur, review_id, "reassigned", f"Reassigned to {new_ds_name}")
        conn.commit()


def mark_reminder_sent(review_id: str, which: str) -> None:
    """which: '7day' | '2day' | 'overdue'"""
    column = {
        "7day": "REMINDER_7DAY_SENT_AT",
        "2day": "REMINDER_2DAY_SENT_AT",
        "overdue": "OVERDUE_ESCALATED_AT",
    }[which]
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""UPDATE {config.REVIEW_INVENTORY_TABLE}
                SET {column} = CURRENT_TIMESTAMP()
                WHERE REVIEW_ID = %s""",
            (review_id,),
        )
        _log_event(cur, review_id, "reminder_sent", which)
        conn.commit()
