
from src.recurrence_detector import (
    identify_issue,
    normalize_issue_title,
    detect_recurring_issues,
)


def test_normalize_issue_title():
    result = normalize_issue_title("  High Missing CustomerID!  ")

    assert result == "high missing customerid"


def test_similar_titles_map_to_same_issue():
    first = identify_issue("High Missing CustomerID")
    second = identify_issue("Missing CustomerID Detected")

    assert first == "MISSING_CUSTOMER_ID"
    assert second == "MISSING_CUSTOMER_ID"


def test_detect_recurring_issue():
    historical_reports = [
        {
            "id": 2,
            "run_timestamp": "2026-10-24T10:00:00",
            "findings": [
                {
                    "title": "Missing CustomerID Detected",
                    "severity": "medium",
                }
            ],
        },
        {
            "id": 1,
            "run_timestamp": "2026-10-23T10:00:00",
            "findings": [
                {
                    "title": "High Missing CustomerID",
                    "severity": "high",
                }
            ],
        },
    ]

    result = detect_recurring_issues(
        historical_reports,
        minimum_occurrences=2,
    )

    assert len(result) == 1
    assert result[0]["issue_id"] == "MISSING_CUSTOMER_ID"
    assert result[0]["occurrences"] == 2


def test_single_occurrence_is_not_recurring():
    historical_reports = [
        {
            "id": 1,
            "run_timestamp": "2026-10-24T10:00:00",
            "findings": [
                {
                    "title": "Missing CustomerID",
                    "severity": "medium",
                }
            ],
        }
    ]

    result = detect_recurring_issues(
        historical_reports,
        minimum_occurrences=2,
    )

    assert result == []


def test_empty_history_returns_empty_list():
    result = detect_recurring_issues([])

    assert result == []

