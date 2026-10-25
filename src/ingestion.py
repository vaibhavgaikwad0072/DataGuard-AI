
from pathlib import Path

import pandas as pd


# Project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset location
DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "Online Retail.xlsx"


def load_retail_data() -> pd.DataFrame:
    """Load the original Online Retail Excel dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    data = pd.read_excel(DATASET_PATH, engine="openpyxl")

    return data


def inspect_dataset(data: pd.DataFrame) -> None:
    """Display a basic overview of the dataset."""

    print("\n========== DATASET OVERVIEW ==========")
    print(f"Number of rows: {data.shape[0]:,}")
    print(f"Number of columns: {data.shape[1]}")

    print("\nColumn names:")
    print(data.columns.tolist())

    print("\nData types:")
    print(data.dtypes)

    print("\nMissing values:")
    print(data.isnull().sum())

    print("\nDuplicate rows:")
    print(data.duplicated().sum())

    print("\nFirst five records:")
    print(data.head())


if __name__ == "__main__":
    retail_data = load_retail_data()
    inspect_dataset(retail_data)

