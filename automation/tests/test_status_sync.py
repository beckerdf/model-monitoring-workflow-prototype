from datetime import date
from pathlib import Path
from unittest.mock import patch

from automation.status_sync import load_status_updates, sync_status_changes
from automation.review_inventory import Review

FIXTURE = Path(__file__).parent / "fixtures" / "review_status_sample.xlsx"


def test_load_status_updates_reads_spreadsheet():
    updates = load_status_updates(FIXTURE)
    assert updates == {"abc-123": "In Progress", "def-456": "Complete"}


def _fake_review(review_id, status):
    return Review(
        review_id=review_id,
        archer_model_number="MFS-0001",
        model_name="Test Model",
        assigned_ds_email="ds@tfs.com",
        assigned_ds_name="Test DS",
        start_date=date(2026, 1, 1),
        due_date=date(2026, 2, 1),
        status=status,
        completion_date=None,
        assigned_by="Auto",
    )


@patch("automation.status_sync.review_inventory.update_status")
@patch("automation.status_sync.review_inventory.get_open_reviews")
def test_sync_only_pushes_actual_changes(mock_get_open, mock_update):
    # abc-123 is currently "Not Started" in Snowflake, spreadsheet says "In Progress" -> real change
    # def-456 is currently "Complete" in Snowflake, spreadsheet also says "Complete" -> NOT a change,
    # this is exactly the re-trigger scenario the safeguard exists for
    mock_get_open.return_value = [
        _fake_review("abc-123", "Not Started"),
        _fake_review("def-456", "In Progress"),  # spreadsheet says Complete -- this IS a real change
    ]

    changes = sync_status_changes(FIXTURE)

    assert ("abc-123", "Not Started", "In Progress") in changes
    assert ("def-456", "In Progress", "Complete") in changes
    assert mock_update.call_count == 2


@patch("automation.status_sync.review_inventory.update_status")
@patch("automation.status_sync.review_inventory.get_open_reviews")
def test_sync_skips_when_status_unchanged(mock_get_open, mock_update):
    # Both already match the spreadsheet -- nothing should fire
    mock_get_open.return_value = [
        _fake_review("abc-123", "In Progress"),
        _fake_review("def-456", "Complete"),
    ]

    changes = sync_status_changes(FIXTURE)

    assert changes == []
    mock_update.assert_not_called()
