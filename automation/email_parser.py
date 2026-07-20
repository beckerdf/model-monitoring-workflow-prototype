"""
Email parser: pulls Archer Model Number, Model Name, Start Date, and Due Date
out of the governance-generated email body.

*** PLACEHOLDER — REPLACE ONCE THE REAL ARCHER EMAIL TEMPLATE ARRIVES ***

This is built against our best guess of the format, based on the fields
governance has confirmed will be present (Archer Model #, Model Name,
Start in Archer, Final Due Date). The actual subject line and body layout
may differ. When the real email lands:

  1. Save a sample (redact model specifics if needed) into
     tests/fixtures/sample_governance_email.txt
  2. Update the regex patterns below to match the real format
  3. Re-run tests/test_email_parser.py against the real sample — it should
     pass once the patterns are correct

Everything downstream (rotation_queue, review_inventory, status_sync) does
NOT depend on this module's internals — only on the ParsedReview fields it
returns. So fixing this one file is the entire blast radius of the template
finally arriving.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class ParsedReview:
    archer_model_number: str
    model_name: str
    start_date: date
    due_date: date


# Best-guess patterns based on fields confirmed with governance so far.
# UPDATE THESE once we have a real sample email.
PATTERNS = {
    "archer_model_number": re.compile(r"Archer Model\s*#?:?\s*([A-Za-z0-9\-]+)", re.IGNORECASE),
    "model_name": re.compile(r"Model Name:?\s*(.+)", re.IGNORECASE),
    "start_date": re.compile(r"Start (?:in Archer|Date):?\s*([\d/\-]+)", re.IGNORECASE),
    "due_date": re.compile(r"(?:Final )?Due Date:?\s*([\d/\-]+)", re.IGNORECASE),
}


def _parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {raw!r}")


def parse_email_body(body: str) -> ParsedReview:
    """
    Extract the four required fields from a governance email body.
    Raises ValueError with a clear message if any field can't be found --
    fail loudly rather than silently assign against bad data.
    """
    values = {}
    for field, pattern in PATTERNS.items():
        match = pattern.search(body)
        if not match:
            raise ValueError(
                f"Could not find '{field}' in email body. "
                f"This likely means the email format doesn't match our current "
                f"assumptions -- see the module docstring for how to update the patterns."
            )
        values[field] = match.group(1).strip()

    return ParsedReview(
        archer_model_number=values["archer_model_number"],
        model_name=values["model_name"],
        start_date=_parse_date(values["start_date"]),
        due_date=_parse_date(values["due_date"]),
    )
