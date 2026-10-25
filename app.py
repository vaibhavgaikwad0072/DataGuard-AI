
import streamlit as st
import pandas as pd

from src.quality_engine import analyze_data_quality
from src.transform import transform_retail_data


st.set_page_config(
    page_title="DataGuard AI",
    page_icon="🛡️",
    layout="wide",
)


st.title("🛡️ DataGuard AI")
st.caption(
    "AI-powered data quality monitoring and investigation"
)

st.divider()


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select a module",
    [
        "Overview",
        "Data Quality",
        "Data Transformation",
    ],
)


# --------------------------------------------------
# Dataset loading
# --------------------------------------------------

st.sidebar.subheader("Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV or Excel file",
    type=["csv", "xlsx"],
)



def load_uploaded_data(file):
    """Load a CSV or Excel file into a DataFrame."""

    if file.name.lower().endswith(".csv"):
        data = pd.read_csv(file)
    else:
        data = pd.read_excel(file)

    # Normalize mixed-type identifier columns for display compatibility.
    if "StockCode" in data.columns:
        data["StockCode"] = data["StockCode"].astype("string")

    return data




data = None

if uploaded_file is not None:
    try:
        data = load_uploaded_data(uploaded_file)

        st.sidebar.success(
            f"Loaded {len(data):,} rows"
        )

    except Exception as error:
        st.sidebar.error(
            f"Could not load the dataset: {error}"
        )


# --------------------------------------------------
# Overview
# --------------------------------------------------

if page == "Overview":

    st.subheader("Project Overview")

    st.write(
        "Upload a dataset using the sidebar to begin "
        "data quality analysis."
    )

    if data is not None:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Rows",
                f"{len(data):,}",
            )

        with col2:
            st.metric(
                "Total Columns",
                f"{len(data.columns):,}",
            )

        with col3:
            st.metric(
                "Missing Cells",
                f"{int(data.isna().sum().sum()):,}",
            )

        with st.expander("Preview dataset"):
            st.dataframe(
                data.head(100),
                width="stretch",
            )

    else:
        st.info(
            "Upload a dataset to see its overview."
        )


# --------------------------------------------------
# Data Quality
# --------------------------------------------------

elif page == "Data Quality":

    st.subheader("Data Quality Analysis")

    if data is None:

        st.info(
            "Upload a dataset to analyze its quality."
        )

    else:

        if st.button(
            "Run Quality Analysis",
            type="primary",
        ):

            try:
                report = analyze_data_quality(data)

                st.session_state["quality_report"] = report

            except Exception as error:
                st.error(
                    f"Quality analysis failed: {error}"
                )

        report = st.session_state.get("quality_report")

        if report is not None:

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Completeness",
                f"{report['completeness_score']:.2f}%",
            )

            col2.metric(
                "Duplicate Rows",
                f"{report['duplicate_rows']:,}",
            )

            col3.metric(
                "Detected Issues",
                f"{report['total_issues']:,}",
            )

            st.subheader("Missing Values")

            missing_data = pd.DataFrame(
                [
                    {
                        "Column": column,
                        "Missing Count": details["missing_count"],
                        "Missing Percentage": details[
                            "missing_percentage"
                        ],
                    }
                    for column, details
                    in report["missing_values"].items()
                ]
            )

            st.dataframe(
                missing_data,
                use_container_width=True,
            )

            st.subheader("Detected Issues")

            if report["issues"]:

                issues_data = pd.DataFrame(
                    report["issues"]
                )

                st.dataframe(
                    issues_data,
                    use_container_width=True,
                )

            else:

                st.success(
                    "No issues were detected by the current checks."
                )

            st.download_button(
                label="Download Quality Report",
                data=pd.Series(report).to_json(
                    indent=2,
                    force_ascii=False,
                ),
                file_name="dataguard_quality_report.json",
                mime="application/json",
            )


# --------------------------------------------------
# Data Transformation
# --------------------------------------------------

elif page == "Data Transformation":

    st.subheader("Data Transformation")

    if data is None:

        st.info(
            "Upload a dataset to inspect its transformation results."
        )

    else:

        st.warning(
            "Transformations are applied to a separate copy. "
            "The uploaded source DataFrame is not modified."
        )

        if st.button(
            "Run Transformation",
            type="primary",
        ):

            try:

                cleaned_data, transformation_report = (
                    transform_retail_data(data)
                )

                st.session_state["cleaned_data"] = cleaned_data
                st.session_state["transformation_report"] = (
                    transformation_report
                )

            except Exception as error:

                st.error(
                    f"Transformation failed: {error}"
                )

        transformation_report = st.session_state.get(
            "transformation_report"
        )

        if transformation_report is not None:

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Original Rows",
                f"{transformation_report['original_rows']:,}",
            )

            col2.metric(
                "Processed Rows",
                f"{transformation_report['processed_rows']:,}",
            )

            col3.metric(
                "Duplicates Removed",
                f"{transformation_report['duplicate_rows_removed']:,}",
            )

            st.subheader("Transformation Report")

            st.json(transformation_report)

            cleaned_data = st.session_state.get("cleaned_data")

            if cleaned_data is not None:

                st.subheader("Processed Dataset Preview")

                st.dataframe(
                    cleaned_data.head(100),
                    use_container_width=True,
                )

                st.download_button(
                    label="Download Processed CSV",
                    data=cleaned_data.to_csv(index=False),
                    file_name="dataguard_processed_data.csv",
                    mime="text/csv",
                )

