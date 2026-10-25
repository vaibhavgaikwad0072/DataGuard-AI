
import pandas as pd


def transform_retail_data(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """
    Create a processed copy of the retail dataset.

    The original DataFrame is not modified.
    Potential business exceptions are preserved.
    """

    if data.empty:
        raise ValueError("Cannot transform an empty dataset.")

    original_rows = len(data)

    # Work on a copy to preserve the source data.
    cleaned_data = data.copy(deep=True)

    # Standardize whitespace in text columns.
    text_columns = cleaned_data.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        cleaned_data[column] = cleaned_data[column].map(
            lambda value: (
                value.strip()
                if isinstance(value, str)
                else value
            )
        )

    # Standardize blank descriptions as missing values.
    if "Description" in cleaned_data.columns:
        descriptions = cleaned_data["Description"]

        cleaned_data["Description"] = descriptions.replace(
            r"^\s*$",
            pd.NA,
            regex=True,
        )

    # Remove exact duplicate rows only from the processed copy.
    duplicate_rows_removed = int(
        cleaned_data.duplicated().sum()
    )

    cleaned_data = cleaned_data.drop_duplicates().copy()

    # Report what changed.
    transformation_report = {
        "original_rows": int(original_rows),
        "processed_rows": int(len(cleaned_data)),
        "duplicate_rows_removed": duplicate_rows_removed,
        "rows_removed": int(
            original_rows - len(cleaned_data)
        ),
        "missing_customer_ids_preserved": int(
            cleaned_data["CustomerID"].isna().sum()
        ) if "CustomerID" in cleaned_data.columns else None,
    }

    return cleaned_data, transformation_report

