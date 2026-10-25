
import pandas as pd
import pytest

from src.quality_engine import (
    EXPECTED_COLUMNS,
    analyze_data_quality,
    print_quality_report,
)


def create_sample_data():
    """Create a small, valid retail dataset for testing."""

    return pd.DataFrame({
        "InvoiceNo": ["536365", "536366", "536367"],
        "StockCode": ["85123A", "71053", "84406B"],
        "Description": [
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "WHITE METAL LANTERN",
            "CREAM CUPID HEARTS COAT HANGER",
        ],
        "Quantity": [6, 4, 8],
        "InvoiceDate": pd.to_datetime([
            "2010-12-01",
            "2010-12-02",
            "2010-12-03",
        ]),
        "UnitPrice": [2.55, 3.39, 2.75],
        "CustomerID": [17850.0, 17850.0, 13047.0],
        "Country": ["United Kingdom", "United Kingdom", "France"],
    })


def find_issue(report, issue_name):
    """Find an issue in the quality report by its identifier."""

    for issue in report["issues"]:
        if issue["issue"] == issue_name:
            return issue

    return None


def test_valid_dataset_has_no_quality_issues():
    data = create_sample_data()

    report = analyze_data_quality(data)

    assert report["total_rows"] == 3
    assert report["total_columns"] == 8
    assert report["missing_columns"] == []
    assert report["unexpected_columns"] == []
    assert report["duplicate_rows"] == 0
    assert report["missing_cells"] == 0
    assert report["completeness_score"] == 100.0
    assert report["total_issues"] == 0


def test_missing_customer_ids_are_detected():
    data = create_sample_data()
    data.loc[0, "CustomerID"] = float("nan")

    report = analyze_data_quality(data)

    issue = find_issue(report, "missing_customer_id")

    assert issue is not None
    assert issue["count"] == 1
    assert issue["severity"] == "medium"
    assert report["missing_values"]["CustomerID"]["missing_count"] == 1
    assert report["missing_values"]["CustomerID"]["missing_percentage"] == 33.33
    assert report["completeness_score"] < 100.0


def test_missing_required_column_is_detected():
    data = create_sample_data().drop(columns=["Country"])

    report = analyze_data_quality(data)

    assert "Country" in report["missing_columns"]

    issue = find_issue(report, "missing_required_column")

    assert issue is not None
    assert issue["column"] == "Country"
    assert issue["severity"] == "critical"


def test_unexpected_column_is_reported():
    data = create_sample_data()
    data["ExtraField"] = ["A", "B", "C"]

    report = analyze_data_quality(data)

    assert "ExtraField" in report["unexpected_columns"]
    assert report["total_columns"] == 9


def test_duplicate_rows_are_detected():
    data = create_sample_data()
    data = pd.concat(
        [data, data.iloc[[0]]],
        ignore_index=True,
    )

    report = analyze_data_quality(data)

    issue = find_issue(report, "duplicate_records")

    assert report["duplicate_rows"] == 1
    assert issue is not None
    assert issue["count"] == 1
    assert issue["severity"] == "medium"


def test_negative_quantities_are_flagged_as_information():
    data = create_sample_data()
    data.loc[0, "Quantity"] = -2

    report = analyze_data_quality(data)

    issue = find_issue(report, "negative_quantity")

    assert issue is not None
    assert issue["count"] == 1
    assert issue["severity"] == "info"


def test_negative_unit_prices_are_detected():
    data = create_sample_data()
    data.loc[0, "UnitPrice"] = -5.0

    report = analyze_data_quality(data)

    issue = find_issue(report, "negative_unit_price")

    assert issue is not None
    assert issue["count"] == 1
    assert issue["severity"] == "high"


def test_zero_unit_prices_are_detected():
    data = create_sample_data()
    data.loc[0, "UnitPrice"] = 0.0

    report = analyze_data_quality(data)

    issue = find_issue(report, "zero_unit_price")

    assert issue is not None
    assert issue["count"] == 1
    assert issue["severity"] == "low"


def test_missing_product_descriptions_are_detected():
    data = create_sample_data()
    data.loc[0, "Description"] = None

    report = analyze_data_quality(data)

    issue = find_issue(report, "missing_product_description")

    assert issue is not None
    assert issue["count"] == 1


def test_cancellation_invoice_numbers_are_detected():
    data = create_sample_data()
    data.loc[0, "InvoiceNo"] = "C536365"

    report = analyze_data_quality(data)

    issue = find_issue(report, "cancelled_transactions")

    assert issue is not None
    assert issue["count"] == 1
    assert issue["severity"] == "info"


def test_empty_dataset_raises_value_error():
    data = pd.DataFrame(columns=EXPECTED_COLUMNS)

    with pytest.raises(ValueError, match="input dataset is empty"):
        analyze_data_quality(data)


def test_quality_analysis_does_not_modify_input_data():
    data = create_sample_data()
    original_data = data.copy(deep=True)

    analyze_data_quality(data)

    pd.testing.assert_frame_equal(data, original_data)


def test_print_quality_report(capsys):
    report = analyze_data_quality(create_sample_data())

    print_quality_report(report)

    output = capsys.readouterr().out

    assert "DATAGUARD QUALITY REPORT" in output
    assert "Total rows: 3" in output
    assert "Completeness score: 100.0%" in output

