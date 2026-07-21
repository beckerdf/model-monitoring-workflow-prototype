from datetime import date

import pytest

from automation.email_parser import parse_email_body, DEFAULT_CYCLE_DAYS

# Real format, confirmed against an actual Archer notification (7/2026)
SAMPLE_BODY = """
Hello,

You are receiving this notification as the model monitoring process is scheduled to start on: 7/6/2026

Model Record Name: Service Ops Credit Loss

No action is required at this time, however, please plan on beginning the monitoring as scheduled.
"""


def test_parses_model_name_and_start_date():
    result = parse_email_body(SAMPLE_BODY)
    assert result.model_name == "Service Ops Credit Loss"
    assert result.start_date == date(2026, 7, 6)


def test_due_date_computed_from_cycle_length():
    result = parse_email_body(SAMPLE_BODY)
    assert result.due_date == date(2026, 7, 6) + __import__("datetime").timedelta(days=DEFAULT_CYCLE_DAYS)
    # matches the real 49-day pattern observed in the Archer report
    assert result.due_date == date(2026, 8, 24)


def test_custom_cycle_length_can_be_passed():
    result = parse_email_body(SAMPLE_BODY, cycle_days=30)
    assert result.due_date == date(2026, 8, 5)


def test_raises_clear_error_when_format_does_not_match():
    with pytest.raises(ValueError, match="Could not find"):
        parse_email_body("This email doesn't match our confirmed format at all.")
