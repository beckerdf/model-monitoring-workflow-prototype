from datetime import date
from pathlib import Path

from automation.rotation_queue import load_rotation_queue, next_assignee

FIXTURE = Path(__file__).parent / "fixtures" / "rotation_queue_sample.xlsx"


def test_load_rotation_queue_reads_all_active_and_inactive_rows():
    people = load_rotation_queue(FIXTURE)
    assert len(people) == 4
    names = {p.full_name for p in people}
    assert "Priya Nguyen" in names
    assert "Sean OBrien" in names  # inactive, but still loaded -- filtering happens at assignment time


def test_inactive_person_is_never_eligible():
    people = load_rotation_queue(FIXTURE)
    sean = next(p for p in people if p.first_name == "Sean")
    assert sean.active is False
    assert sean.is_eligible_on(date(2026, 7, 20)) is False


def test_person_on_vacation_is_ineligible_during_range_only():
    people = load_rotation_queue(FIXTURE)
    rohan = next(p for p in people if p.first_name == "Rohan")
    assert rohan.is_unavailable_on(date(2026, 7, 20)) is True   # inside range
    assert rohan.is_unavailable_on(date(2026, 7, 26)) is False  # day after range ends
    assert rohan.is_unavailable_on(date(2026, 7, 13)) is False  # day before range starts


def test_next_assignee_picks_oldest_last_assigned_among_eligible():
    people = load_rotation_queue(FIXTURE)
    # On 2026-07-20: Sean is inactive, Rohan is on vacation.
    # Remaining eligible: Marcus (2026-05-18) and Priya (2026-06-02).
    # Marcus has the older date, so he should be picked.
    winner = next_assignee(people, as_of=date(2026, 7, 20))
    assert winner.first_name == "Marcus"


def test_next_assignee_returns_none_when_nobody_eligible():
    people = load_rotation_queue(FIXTURE)
    for p in people:
        p.active = False
    assert next_assignee(people, as_of=date(2026, 7, 20)) is None
