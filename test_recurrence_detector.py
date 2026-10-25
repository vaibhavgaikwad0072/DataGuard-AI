
from src.recurrence_detector import detect_recurring_issues


def main():
    sample_history = [
        {
            "id": 3,
            "run_timestamp": "2026-10-25T10:00:00+00:00",
            "findings": [
                {
                    "title": "High Missing CustomerID",
                    "severity": "high",
                },
                {
                    "title": "Duplicate Records Detected",
                    "severity": "medium",
                },
            ],
        },
        {
            "id": 2,
            "run_timestamp": "2026-10-24T20:00:00+00:00",
            "findings": [
                {
                    "title": "High missing CustomerID!",
                    "severity": "medium",
                },
                {
                    "title": "Duplicate Records Detected",
                    "severity": "medium",
                },
            ],
        },
        {
            "id": 1,
            "run_timestamp": "2026-10-24T19:00:00+00:00",
            "findings": [
                {
                    "title": "Negative Quantities Present",
                    "severity": "low",
                },
            ],
        },
    ]

    recurring_issues = detect_recurring_issues(sample_history)

    print("RECURRING ISSUE DETECTION")
    print("=" * 50)

    if not recurring_issues:
        print("No recurring issues found.")
        return

    for issue in recurring_issues:
        print(f"\nIssue: {issue['issue']}")
        print(f"Occurrences: {issue['occurrences']}")
        print(f"Latest severity: {issue['latest_severity']}")
        print(f"Investigation IDs: {issue['investigation_ids']}")


if __name__ == "__main__":
    main()

