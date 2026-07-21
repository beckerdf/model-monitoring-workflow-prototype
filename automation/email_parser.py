"""
Email parser: pulls the Model Record Name and Start Date out of the
Archer-generated "Model Monitoring Notification" email, and computes a
due date from a fixed monitoring-cycle length.

*** ASSUMPTION TO CONFIRM: 49-day (7-week) cycle from start to due date. ***
This was inferred from three real start/due pairs in an Archer report (all
exactly 49 days apart, regardless of risk rating) -- not confirmed as an
official policy. Update DEFAULT_CYCLE_DAYS below once confirmed, or replace
the whole due-date calculation if it turns out to vary by risk rating or
model type.

*** REAL EMAIL FORMAT (confirmed 7/2026) ***
This is an "Awareness" notification, not an assignment request -- Archer
sends it to the Model Owner + CC'd stakeholders, with no due date and no
model number in the body. Subject line:
  "Model Monitoring Notification - Submitted for Model Owner and Model
   Reviewer Lead, Awareness"
Body contains only:
  "You are receiving this notification as the model monitoring process is
   scheduled to start on: <date>"
  "Model Record Name: <name>"

There is no Archer Model Number in this email -- Model Record Name is the
only identifier available, so it's used as the key downstream instead.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

DEFAULT_CYCLE_DAYS = 49  # ASSUMPTION -- confirm with governance


@dataclass
class ParsedReview:
    model_name: str
    start_date: date
    due_date: date


PATTERNS = {
    "model_name": re.compile(r"Model Record Name:?\s*([^\n\r]+)", re.IGNORECASE),
    "start_date": re.compile(r"scheduled to start on:?\s*([\d/\-]+)", re.IGNORECASE),
}


def _parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {raw!r}")


def parse_email_body(body: str, cycle_days: int = DEFAULT_CYCLE_DAYS) -> ParsedReview:
    """
    Extract the model name and start date from a governance notification
    email body, and compute a due date using the fixed cycle-length
    assumption. Raises ValueError with a clear message if a required
    field can't be found -- fail loudly rather than silently assign
    against bad data.
    """
    values = {}
    for field, pattern in PATTERNS.items():
        match = pattern.search(body)
        if not match:
            raise ValueError(
                f"Could not find '{field}' in email body. "
                f"This likely means the email format has changed from what "
                f"we've confirmed -- see the module docstring for the expected format."
            )
        values[field] = match.group(1).strip()

    start_date = _parse_date(values["start_date"])

    return ParsedReview(
        model_name=values["model_name"],
        start_date=start_date,
        due_date=start_date + timedelta(days=cycle_days),
    )
