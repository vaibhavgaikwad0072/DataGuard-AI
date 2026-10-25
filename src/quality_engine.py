
from typing import Any

import pandas as pd


EXPECTED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def analyze_data_quality(data: pd.DataFrame) -> dict[str, Any]:
    """
    Analyze the quality of an online retail transaction dataset.

    The function reports potential data quality issues without
    modifying or deleting records.
    """

    if data.empty:
        raise ValueError("The input dataset is empty.")

    # --------------------------------------------------
    # 1. Schema validation
    # --------------------------------------------------

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in data.columns
    ]

    unexpected_columns = [
        column
        for column in data.columns
        if column not in EXPECTED_COLUMNS
    ]

    # --------------------------------------------------
    # 2. Missing value analysis
    # --------------------------------------------------

    missing_values = data.isnull().sum()

    missing_report = {}

    for column, count in missing_values.items():
        missing_report[column] = {
            "missing_count": int(count),
            "missing_percentage": round(
                count / len(data) * 100, 2
            ),
        }

    # --------------------------------------------------
    # 3. Duplicate analysis
    # --------------------------------------------------

    duplicate_count = int(data.duplicated().sum())

    # --------------------------------------------------
    # 4. Business rule checks
    # --------------------------------------------------

    issues = []

    # Missing schema fields
    for column in missing_columns:
        issues.append({
            "issue": "missing_required_column",
            "column": column,
            "count": None,
            "severity": "critical",
            "description": (
                f"Required column '{column}' is missing."
            ),
        })

    # Missing product descriptions
    if "Description" in data.columns:
        count = int(data["Description"].isna().sum())

        if count:
            issues.append({
                "issue": "missing_product_description",
                "column": "Description",
                "count": count,
                "severity": "low",
                "description": (
                    "Some transactions have no product description."
                ),
            })

    # Missing customer IDs
    if "CustomerID" in data.columns:
        count = int(data["CustomerID"].isna().sum())

        if count:
            issues.append({
                "issue": "missing_customer_id",
                "column": "CustomerID",
                "count": count,
                "severity": "medium",
                "description": (
                    "Some transactions cannot be directly linked "
                    "to a known customer."
                ),
            })

    # Exact duplicate records
    if duplicate_count:
        issues.append({
            "issue": "duplicate_records",
            "column": None,
            "count": duplicate_count,
            "severity": "medium",
            "description": (
                "Exact duplicate rows were detected. "
                "Review them before deciding whether to remove them."
            ),
        })

    # Negative quantities may represent returns or cancellations.
    if "Quantity" in data.columns:
        count = int((data["Quantity"] < 0).sum())

        if count:
            issues.append({
                "issue": "negative_quantity",
                "column": "Quantity",
                "count": count,
                "severity": "info",
                "description": (
                    "Negative quantities may represent returns "
                    "or credit transactions. Investigate rather "
                    "than automatically treating them as errors."
                ),
            })

    # Negative unit prices need investigation.
    if "UnitPrice" in data.columns:
        count = int((data["UnitPrice"] < 0).sum())

        if count:
            issues.append({
                "issue": "negative_unit_price",
                "column": "UnitPrice",
                "count": count,
                "severity": "high",
                "description": (
                    "Negative unit prices were found and require "
                    "business-rule investigation."
                ),
            })

    # Zero prices are flagged for review, not automatically rejected.
    if "UnitPrice" in data.columns:
        count = int((data["UnitPrice"] == 0).sum())

        if count:
            issues.append({
                "issue": "zero_unit_price",
                "column": "UnitPrice",
                "count": count,
                "severity": "low",
                "description": (
                    "Transactions with zero unit prices require review."
                ),
            })

    # Invoice numbers beginning with C commonly indicate cancellations
    # in this dataset. This is an informational business metric.
    if "InvoiceNo" in data.columns:
        cancellation_mask = (
            data["InvoiceNo"]
            .astype("string")
            .str.startswith("C", na=False)
        )

        cancellation_count = int(cancellation_mask.sum())

        if cancellation_count:
            issues.append({
                "issue": "cancelled_transactions",
                "column": "InvoiceNo",
                "count": cancellation_count,
                "severity": "info",
                "description": (
                    "Invoice numbers beginning with 'C' were found. "
                    "Review these as potential cancellations."
                ),
            })

    # --------------------------------------------------
    # 5. Calculate an initial data quality score
    # --------------------------------------------------

    # This score measures completeness only. It does not yet
    # measure every type of data quality.
    total_cells = data.shape[0] * data.shape[1]
    missing_cells = int(data.isnull().sum().sum())

    completeness_score = round(
        (1 - missing_cells / total_cells) * 100, 2
    )

    # --------------------------------------------------
    # 6. Build the report
    # --------------------------------------------------

    report = {
        "total_rows": int(data.shape[0]),
        "total_columns": int(data.shape[1]),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "missing_values": missing_report,
        "duplicate_rows": duplicate_count,
        "missing_cells": missing_cells,
        "completeness_score": completeness_score,
        "total_issues": len(issues),
        "issues": issues,
    }

    return report


def print_quality_report(report: dict[str, Any]) -> None:
    """Print a readable summary of the quality report."""

    print("\n========== DATAGUARD QUALITY REPORT ==========")

    print(f"Total rows: {report['total_rows']:,}")
    print(f"Total columns: {report['total_columns']}")
    print(f"Duplicate rows: {report['duplicate_rows']:,}")

    print(
        f"Completeness score: "
        f"{report['completeness_score']}%"
    )

    print(f"Total issue types detected: {report['total_issues']}")

    print("\nMissing values by column:")

    for column, details in report["missing_values"].items():
        print(
            f"  {column}: "
            f"{details['missing_count']:,} "
            f"({details['missing_percentage']}%)"
        )

    print("\nDetected issues:")

    for issue in report["issues"]:
        print(
            f"  [{issue['severity'].upper()}] "
            f"{issue['issue']}: "
            f"{issue['count']} records"
        )

        print(f"    {issue['description']}")

