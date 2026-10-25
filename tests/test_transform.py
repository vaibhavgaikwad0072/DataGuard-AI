
import pandas as pd
import pytest

from src.transform import transform_retail_data


def create_sample_data():
    """Create a small retail dataset for transformation tests."""

    return pd.DataFrame({
        "InvoiceNo": ["536365", "536366", "536367"],
        "StockCode": ["85123A", "71053", "84406B"],
        "Description": [
            " WHITE HANGING HEART T-LIGHT HOLDER ",
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
        "Country": [
            " United Kingdom ",
            "United Kingdom",
            " France ",
        ],
    })


def test_transformation_returns_dataframe_and_report():
    data = create_sample_data()

    cleaned_data, report = transform_retail_data(data)

    assert isinstance(cleaned_data, pd.DataFrame)
    assert isinstance(report, dict)


def test_transformation_preserves_original_data():
    data = create_sample_data()
    original_data = data.copy(deep=True)

    transform_retail_data(data)

    pd.testing.assert_frame_equal(data, original_data)


def test_leading_and_trailing_whitespace_is_removed():
    data = create_sample_data()

    cleaned_data, _ = transform_retail_data(data)

    assert cleaned_data.loc[0, "Description"] == (
        "WHITE HANGING HEART T-LIGHT HOLDER"
    )
    assert cleaned_data.loc[0, "Country"] == "United Kingdom"
    assert cleaned_data.loc[2, "Country"] == "France"


def test_exact_duplicate_rows_are_removed():
    data = create_sample_data()

    data = pd.concat(
        [data, data.iloc[[0]]],
        ignore_index=True,
    )

    cleaned_data, report = transform_retail_data(data)

    assert len(cleaned_data) == 3
    assert report["duplicate_rows_removed"] == 1
    assert report["rows_removed"] == 1


def test_non_duplicate_rows_are_preserved():
    data = create_sample_data()

    cleaned_data, report = transform_retail_data(data)

    assert len(cleaned_data) == 3
    assert report["duplicate_rows_removed"] == 0
    assert report["rows_removed"] == 0


def test_blank_descriptions_are_converted_to_missing_values():
    data = create_sample_data()
    data.loc[0, "Description"] = "   "

    cleaned_data, _ = transform_retail_data(data)

    assert pd.isna(cleaned_data.loc[0, "Description"])


def test_missing_customer_ids_are_preserved():
    data = create_sample_data()
    data.loc[0, "CustomerID"] = float("nan")

    cleaned_data, report = transform_retail_data(data)

    assert cleaned_data["CustomerID"].isna().sum() == 1
    assert report["missing_customer_ids_preserved"] == 1


def test_negative_quantities_are_preserved():
    data = create_sample_data()
    data.loc[0, "Quantity"] = -2

    cleaned_data, _ = transform_retail_data(data)

    assert -2 in cleaned_data["Quantity"].values


def test_negative_unit_prices_are_preserved():
    data = create_sample_data()
    data.loc[0, "UnitPrice"] = -5.0

    cleaned_data, _ = transform_retail_data(data)

    assert -5.0 in cleaned_data["UnitPrice"].values


def test_zero_unit_prices_are_preserved():
    data = create_sample_data()
    data.loc[0, "UnitPrice"] = 0.0

    cleaned_data, _ = transform_retail_data(data)

    assert 0.0 in cleaned_data["UnitPrice"].values


def test_transformation_report_has_correct_row_counts():
    data = create_sample_data()

    data = pd.concat(
        [data, data.iloc[[1]]],
        ignore_index=True,
    )

    cleaned_data, report = transform_retail_data(data)

    assert report["original_rows"] == 4
    assert report["processed_rows"] == 3
    assert report["duplicate_rows_removed"] == 1
    assert report["rows_removed"] == 1
    assert len(cleaned_data) == report["processed_rows"]


def test_missing_customer_id_report_is_none_without_column():
    data = create_sample_data().drop(columns=["CustomerID"])

    cleaned_data, report = transform_retail_data(data)

    assert "CustomerID" not in cleaned_data.columns
    assert report["missing_customer_ids_preserved"] is None


def test_empty_dataset_raises_value_error():
    data = pd.DataFrame(columns=[
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ])

    with pytest.raises(
        ValueError,
        match="Cannot transform an empty dataset",
    ):
        transform_retail_data(data)

