"""
Rotation Queue: reads the shared spreadsheet national managers maintain and
determines who's next in line for a model monitoring review assignment.

This module only ever READS the spreadsheet. It never writes to it — that's
a deliberate design decision so a manager's or DS's entry is never silently
overwritten by the automation.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

REQUIRED_COLUMNS = [
    "Last Name", "First Name", "Email Address", "Active",
    "Unavailable Start Date", "Unavailable End Date", "Last Assigned Date",
]


@dataclass
class DataScientist:
    last_name: str
    first_name: str
    email: str
    active: bool
    unavailable_start: Optional[date]
    unavailable_end: Optional[date]
    last_assigned: Optional[date]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_unavailable_on(self, as_of: date) -> bool:
        if self.unavailable_start is None or self.unavailable_end is None:
            return False
        return self.unavailable_start <= as_of <= self.unavailable_end

    def is_eligible_on(self, as_of: date) -> bool:
        return self.active and not self.is_unavailable_on(as_of)


def _to_date(value) -> Optional[date]:
    if pd.isna(value) or value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def load_rotation_queue(path: Path) -> list[DataScientist]:
    """Read the Rotation Queue spreadsheet into a list of DataScientist records."""
    df = pd.read_excel(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Rotation Queue spreadsheet is missing required column(s): {missing}. "
            f"Expected columns: {REQUIRED_COLUMNS}"
        )

    people = []
    for _, row in df.iterrows():
        if pd.isna(row["Email Address"]):
            continue  # skip blank rows
        people.append(DataScientist(
            last_name=str(row["Last Name"]).strip(),
            first_name=str(row["First Name"]).strip(),
            email=str(row["Email Address"]).strip(),
            active=bool(row["Active"]),
            unavailable_start=_to_date(row["Unavailable Start Date"]),
            unavailable_end=_to_date(row["Unavailable End Date"]),
            last_assigned=_to_date(row["Last Assigned Date"]),
        ))
    return people


def next_assignee(people: list[DataScientist], as_of: date) -> Optional[DataScientist]:
    """
    Return the eligible DataScientist with the oldest Last Assigned Date
    (never-assigned people, i.e. last_assigned is None, are treated as
    the oldest possible and go first). Returns None if nobody is eligible.
    """
    eligible = [p for p in people if p.is_eligible_on(as_of)]
    if not eligible:
        return None
    return min(eligible, key=lambda p: (p.last_assigned is not None, p.last_assigned or date.min))
