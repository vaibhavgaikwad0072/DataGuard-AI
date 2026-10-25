
from collections import defaultdict
import re


ISSUE_PATTERNS = {
    "MISSING_CUSTOMER_ID": [
        "customerid",
        "customer id",
    ],
    "DUPLICATE_ROWS": [
        "duplicate",
    ],
    "NEGATIVE_UNIT_PRICE": [
        "negative unit price",
    ],
    "ZERO_UNIT_PRICE": [
        "zero unit price",
    ],
    "MISSING_DESCRIPTION": [
        "missing product description",
        "missing description",
    ],
    "NEGATIVE_QUANTITY": [
        "negative quantity",
    ],
}


def normalize_issue_title(title: str) -> str:
    """Normalize a finding title before matching."""

    normalized = title.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def identify_issue(title: str) -> str:
    """Map a finding title to a stable issue identifier."""

    normalized_title = normalize_issue_title(title)

    for issue_id, patterns in ISSUE_PATTERNS.items():
        for pattern in patterns:
            if pattern in normalized_title:
                return issue_id

    return normalized_title


def detect_recurring_issues(
    historical_reports: list[dict],
    minimum_occurrences: int = 2,
) -> list[dict]:
    """Detect issues appearing across multiple investigations."""

    issue_records = defaultdict(list)

    for report in historical_reports:
        report_id = report.get("id")
        timestamp = report.get("run_timestamp")

        for finding in report.get("findings", []):
            title = finding.get("title", "").strip()

            if not title:
                continue

            issue_id = identify_issue(title)

            issue_records[issue_id].append({
                "title": title,
                "severity": finding.get("severity", "unknown"),
                "investigation_id": report_id,
                "timestamp": timestamp,
            })

    recurring_issues = []

    for issue_id, records in issue_records.items():
        unique_reports = {
            record["investigation_id"]
            for record in records
        }

        if len(unique_reports) < minimum_occurrences:
            continue

        latest_record = records[0]

        recurring_issues.append({
            "issue_id": issue_id,
            "issue": latest_record["title"],
            "occurrences": len(unique_reports),
            "latest_severity": latest_record["severity"],
            "investigation_ids": list(unique_reports),
        })

    recurring_issues.sort(
        key=lambda issue: issue["occurrences"],
        reverse=True,
    )

    return recurring_issues

