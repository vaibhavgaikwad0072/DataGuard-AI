
from src.ingestion import load_retail_data
from src.drift_detector import analyze_historical_drift


def main():
    print("Loading retail dataset...")

    data = load_retail_data()

    print("\nAnalyzing historical data drift...")

    results = analyze_historical_drift(
        data,
        periods=4,
    )

    print("\n========== HISTORICAL DRIFT REPORT ==========")

    for result in results:
        print(
            f"\nPeriod {result['previous_period']} "
            f"-> Period {result['current_period']}"
        )

        print(
            f"Drift alerts: {result['drift_count']}"
        )

        for comparison in result["comparisons"]:
            status = (
                "DRIFT DETECTED"
                if comparison["drift_detected"]
                else "NORMAL"
            )

            print(f"\nMetric: {comparison['metric']}")
            print(f"Previous: {comparison['previous_value']}")
            print(f"Current: {comparison['current_value']}")
            print(f"Change: {comparison['change']}")
            print(f"Threshold: {comparison['threshold']}")
            direction = comparison.get("direction", "normal")
            print(f"Status: {status}")
            print(f"Direction: {direction}")





if __name__ == "__main__":
    main()

