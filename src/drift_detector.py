

import numpy as np
import pandas as pd

def calculate_batch_metrics(
    data: pd.DataFrame,
) -> dict:
    """Calculate quality and statistical metrics for one batch."""

    if data.empty:
        raise ValueError("Cannot analyze an empty batch.")

    metrics = {
        "row_count": int(len(data)),
        "missing_customer_id_pct": None,
        "duplicate_row_pct": round(
            data.duplicated().mean() * 100, 2
        ),
        "average_unit_price": None,
    }

    if "CustomerID" in data.columns:
        metrics["missing_customer_id_pct"] = round(
            data["CustomerID"].isna().mean() * 100, 2
        )

    if "UnitPrice" in data.columns:
        metrics["average_unit_price"] = round(
            data["UnitPrice"].mean(), 4
        )

    return metrics


def compare_batches(
    previous: dict,
    current: dict,
    thresholds: dict | None = None,
) -> dict:
    """
    Compare two batches and flag changes exceeding
    configurable thresholds.

    Thresholds represent absolute percentage-point changes
    for percentages and relative percentage changes for price.
    """

    if thresholds is None:
        thresholds = {
            "missing_customer_id_pct": 5,
            "duplicate_row_pct": 5,
            "average_unit_price_pct": 10,
        }

    comparisons = []

    # Compare percentage-based metrics.
    for metric in [
        "missing_customer_id_pct",
        "duplicate_row_pct",
    ]:
        previous_value = previous.get(metric)
        current_value = current.get(metric)

        if previous_value is None or current_value is None:
            continue

        change = round(current_value - previous_value, 2)

        drift_detected = abs(change) >= thresholds[metric]
        direction = (
            "deterioration" if change > 0 else "improvement"
        ) if drift_detected else "normal"

        comparisons.append({
            "metric": metric,
            "previous_value": previous_value,
            "current_value": current_value,
            "change": change,
            "threshold": thresholds[metric],
            "drift_detected": drift_detected,
            "direction": direction,
        })

    # Compare average price using relative percentage change.
    previous_price = previous.get("average_unit_price") 
    current_price = current.get("average_unit_price")

    if ( previous_price is not None and current_price is not None and previous_price != 0 ):
        change_pct = round( (current_price - previous_price) / abs(previous_price) * 100, 2, )
        threshold = thresholds["average_unit_price_pct"]
        drift_detected = abs(change_pct) >= threshold

        if drift_detected and change_pct > 0: 
            direction = "increase" 
        elif drift_detected and change_pct < 0: 
            direction = "decrease" 
        else: 
            direction = "normal" 
        comparisons.append({ "metric": "average_unit_price", "previous_value": previous_price, "current_value": current_price, "change": change_pct, "threshold": threshold, "drift_detected": drift_detected, "direction": direction, })

    return {
        "previous_batch_rows": previous["row_count"],
        "current_batch_rows": current["row_count"],
        "comparisons": comparisons,
        "drift_count": sum(
            item["drift_detected"]
            for item in comparisons
        ),
    }


def analyze_historical_drift(
    data: pd.DataFrame,
    periods: int = 4,
) -> list[dict]:
    """
    Split transactions into chronological periods and
    compare each period with the preceding period.
    """

    required_columns = {"InvoiceDate"}

    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if periods < 2:
        raise ValueError("Use at least two periods.")

    ordered_data = data.copy()

    ordered_data["InvoiceDate"] = pd.to_datetime(
        ordered_data["InvoiceDate"],
        errors="coerce",
    )

    ordered_data = ordered_data.dropna(
        subset=["InvoiceDate"]
    ).sort_values("InvoiceDate")

    if len(ordered_data) < periods:
        raise ValueError(
            "Not enough valid records to create the requested periods."
        )

    # Split in chronological order while keeping records intact.
    batch_arrays = np.array_split(
        np.arange(len(ordered_data)),
        periods,
    )

    batches = [
        ordered_data.iloc[indices].copy()
        for indices in batch_arrays
        if len(indices) > 0
    ]

    batch_metrics = [
        calculate_batch_metrics(batch)
        for batch in batches
    ]

    results = []

    for index in range(1, len(batch_metrics)):
        comparison = compare_batches(
            batch_metrics[index - 1],
            batch_metrics[index],
        )

        comparison["previous_period"] = index
        comparison["current_period"] = index + 1

        results.append(comparison)

    return results



