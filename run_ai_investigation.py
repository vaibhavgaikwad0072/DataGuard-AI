
from src.ingestion import load_retail_data
from src.quality_engine import analyze_data_quality
from src.drift_detector import analyze_historical_drift
from src.ai_investigator import investigate_data
from src.recurrence_detector import detect_recurring_issues

from src.database import (
    initialize_database,
    initialize_investigation_history,
    save_investigation,
    get_investigation_history,
    get_historical_context,
)


def main():
    # Step 1: Initialize database tables
    initialize_database()
    initialize_investigation_history()

    # Step 2: Load dataset
    print("Loading retail dataset...")
    data = load_retail_data()

    # Step 3: Analyze data quality
    print("Analyzing data quality...")
    quality_report = analyze_data_quality(data)

    # Step 4: Detect historical drift
    print("Detecting historical drift...")
    drift_results = analyze_historical_drift(
        data,
        periods=4,
    )

    # Step 5: Retrieve previous investigations
    print("Retrieving historical context...")

    historical_context = get_historical_context(limit=10)
    historical_reports = get_investigation_history(limit=10)

    print(
        f"Previous investigations retrieved: "
        f"{len(historical_context)}"
    )

    # Step 6: Detect recurring issues BEFORE AI investigation
    print("Detecting recurring issues...")

    recurring_issues = detect_recurring_issues(
        historical_reports,
        minimum_occurrences=2,
    )

    print(f"Recurring issues detected: {len(recurring_issues)}")

    for issue in recurring_issues:
        print(
            f"- {issue['issue']} "
            f"(occurrences: {issue['occurrences']}, "
            f"latest severity: {issue['latest_severity']})"
        )

    # Step 7: Run AI investigation ONCE
    print("\nRunning AI investigation...")

    investigation = investigate_data(
        quality_report=quality_report,
        drift_results=drift_results,
        historical_context=historical_context,
        recurring_issues=recurring_issues,
    )

    # Step 8: Save the new investigation
    investigation_id = save_investigation(investigation)

    print(
        f"\nInvestigation saved successfully. "
        f"ID: {investigation_id}"
    )

    # Step 9: Print AI investigation report
    print("\n========== AI INVESTIGATION REPORT ==========")

    print("\nSUMMARY")
    print(investigation.summary)

    for index, finding in enumerate(
        investigation.findings,
        start=1,
    ):
        print(f"\nFINDING {index}: {finding.title}")
        print(f"Severity: {finding.severity}")

        print("\nEvidence:")
        for item in finding.evidence:
            print(f"- {item}")

        print("\nExplanation:")
        print(finding.explanation)

        print("\nRecommended actions:")
        for action in finding.recommended_actions:
            print(f"- {action}")

    print("\nLimitations:")
    for limitation in investigation.limitations:
        print(f"- {limitation}")

    # Step 10: Retrieve and display recent history
    history = get_investigation_history(limit=5)

    print("\n" + "=" * 60)
    print("RECENT INVESTIGATION HISTORY")
    print("=" * 60)

    for previous_report in history:
        print(f"\nInvestigation ID: {previous_report['id']}")
        print(f"Timestamp: {previous_report['run_timestamp']}")
        print(f"Summary: {previous_report['summary']}")
        print(f"Number of findings: {len(previous_report['findings'])}")


if __name__ == "__main__":
    main()

