from datetime import date

import pytest

from automation.email_parser import parse_email_body

SAMPLE_BODY = """
A new model monitoring review has been assigned.

Model Name: Return Rate Model 2.1 - MFS
Archer Model #: MFS-1032
Start in Archer: 6/22/2026
Final Due Date: 8/10/2026
"""


def test_parses_all_fields_from_best_guess_format():
    result = parse_email_body(SAMPLE_BODY)
    assert result.archer_model_number == "MFS-1032"
    assert result.model_name == "Return Rate Model 2.1 - MFS"
    assert result.start_date == date(2026, 6, 22)
    assert result.due_date == date(2026, 8, 10)


def test_raises_clear_error_when_format_does_not_match():
    with pytest.raises(ValueError, match="Could not find"):
        parse_email_body("This email doesn't match our assumed format at all.")
