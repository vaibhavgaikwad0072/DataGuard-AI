
from src.ingestion import load_retail_data
from src.quality_engine import (
    analyze_data_quality,
    print_quality_report,
)
from src.transform import transform_retail_data
from src.database import (
    initialize_database,
    save_transactions,
    save_quality_report,
    get_database_summary,
)


def main():
    print("Loading raw dataset...")

    raw_data = load_retail_data()

    print(f"Raw records: {len(raw_data):,}")

    print("\nAnalyzing source data...")

    quality_report = analyze_data_quality(raw_data)

    print_quality_report(quality_report)

    print("\nApplying transformations...")

    processed_data, transformation_report = (
        transform_retail_data(raw_data)
    )

    print("\n========== ETL SUMMARY ==========")

    for metric, value in transformation_report.items():
        print(f"{metric}: {value}")

    print("\nInitializing SQLite database...")

    initialize_database()

    print("\nSaving processed transactions...")

    save_transactions(processed_data)

    print("\nSaving quality report...")

    save_quality_report(quality_report)

    print("\n========== DATABASE SUMMARY ==========")

    summary = get_database_summary()

    for metric, value in summary.items():
        print(f"{metric}: {value:,}")

    print("\nDataGuard AI ETL pipeline completed successfully.")


if __name__ == "__main__":
    main()

