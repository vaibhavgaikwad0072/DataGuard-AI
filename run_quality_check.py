
from src.ingestion import load_retail_data
from src.quality_engine import (
    analyze_data_quality,
    print_quality_report,
)


def main():
    print("Loading Online Retail dataset...")

    data = load_retail_data()

    print("Running data quality checks...")

    report = analyze_data_quality(data)

    print_quality_report(report)


if __name__ == "__main__":
    main()

