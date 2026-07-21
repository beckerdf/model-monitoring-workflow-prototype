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
    import snowflake.connector

    connect_kwargs = dict(
        account=config.SNOWFLAKE_ACCOUNT,
        user=config.SNOWFLAKE_USER,
        warehouse=config.SNOWFLAKE_WAREHOUSE,
        database=config.SNOWFLAKE_DATABASE,
        schema=config.SNOWFLAKE_SCHEMA,
        role=config.SNOWFLAKE_ROLE,
        authenticator=config.SNOWFLAKE_AUTHENTICATOR,
    )

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
        return
