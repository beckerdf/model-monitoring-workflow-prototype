"""
Review Status sync: reads the shared spreadsheet the DS edits directly and
syncs any CHANGED status into Snowflake. This is the safeguard we flagged
in design: a review sitting at "Complete" must not re-trigger a closure
notification on every run — only an actual transition should fire one.
"""
from pathlib import Path

import pandas as pd

from . import review_inventory

REQUIRED_COLUMNS = ["Review ID", "Status"]
VALID_STATUSES = {"Not Started", "In Progress", "Complete"}


def load_status_updates(path: Path) -> dict[str, str]:
    """Returns {review_id: status} from the shared spreadsheet."""
    df = pd.read_excel(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Review Status spreadsheet is missing required column(s): {missing}. "
            f"Expected columns: {REQUIRED_COLUMNS}"
        )

    updates = {}
    for _, row in df.iterrows():
        review_id = row["Review ID"]
        status = row["Status"]
        if pd.isna(review_id) or pd.isna(status):
            continue
        status = str(status).strip()
        if status not in VALID_STATUSES:
            continue  # ignore malformed entries rather than crash the run
        updates[str(review_id).strip()] = status
    return updates


def sync_status_changes(spreadsheet_path: Path) -> list[tuple[str, str, str]]:
    """
    Compares the spreadsheet's status column against Snowflake's current
    status for each open review, and only pushes an update when it's
    actually different. Returns a list of (review_id, old_status, new_status)
    for whatever actually changed, so the caller can decide what to notify.
    """
    spreadsheet_statuses = load_status_updates(spreadsheet_path)
    open_reviews = review_inventory.get_open_reviews()

    changes = []
    for review in open_reviews:
        new_status = spreadsheet_statuses.get(review.review_id)
        if new_status is None or new_status == review.status:
            continue  # no entry, or no real change -- skip
        review_inventory.update_status(review.review_id, new_status)
        changes.append((review.review_id, review.status, new_status))
    return changes
