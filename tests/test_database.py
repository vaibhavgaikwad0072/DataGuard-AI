
import json
import sqlite3

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

import src.database as database
from src.ai_investigator import InvestigationFinding, InvestigationReport


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create an isolated temporary database for each test."""

    database_path = tmp_path / "test_dataguard.db"

    test_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}"
    )

    monkeypatch.setattr(database, "DATABASE_PATH", database_path)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(
        database,
        "DATABASE_URL",
        f"sqlite:///{database_path.as_posix()}",
    )

    yield database_path, test_engine

    test_engine.dispose()


@pytest.fixture
def sample_quality_report():
    return {
        "total_rows": 100,
        "total_columns": 8,
        "duplicate_rows": 5,
        "missing_cells": 12,
        "completeness_score": 98.5,
        "total_issues": 3,
        "issues": [
            {
                "issue": "missing_customer_id",
                "count": 10,
                "severity": "medium",
            }
        ],
    }


@pytest.fixture
def sample_investigation():
    finding = InvestigationFinding(
        title="Missing Customer IDs",
        severity="medium",
        evidence=["10 customer IDs are missing"],
        explanation="Some transactions cannot be linked to customers.",
        recommended_actions=[
            "Investigate the affected transactions"
        ],
    )

    return InvestigationReport(
        summary="Customer ID completeness requires investigation.",
        findings=[finding],
        limitations=["The reason for missing IDs is unknown."],
    )


def test_initialize_database_creates_quality_reports_table(test_db):
    _, engine = test_db

    database.initialize_database()

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'quality_reports'
            """)
        ).fetchone()

    assert result is not None


def test_initialize_investigation_history_creates_table(test_db):
    database_path, _ = test_db

    database.initialize_investigation_history()

    with sqlite3.connect(database_path) as connection:
        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'investigation_history'
            """
        ).fetchone()

    assert result is not None


def test_save_quality_report(test_db, sample_quality_report):
    _, engine = test_db

    database.save_quality_report(sample_quality_report)

    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT * FROM quality_reports")
        ).mappings().one()

    assert row["total_rows"] == 100
    assert row["total_columns"] == 8
    assert row["duplicate_rows"] == 5
    assert row["missing_cells"] == 12
    assert row["completeness_score"] == 98.5
    assert row["total_issues"] == 3

    stored_report = json.loads(row["report_json"])
    assert stored_report["issues"][0]["issue"] == "missing_customer_id"


def test_save_transactions(test_db):
    _, engine = test_db

    data = pd.DataFrame({
        "InvoiceNo": ["1001", "1002"],
        "Quantity": [2, 3],
        "UnitPrice": [10.0, 15.0],
    })

    database.save_transactions(data)

    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM retail_transactions")
        ).scalar_one()

    assert count == 2


def test_get_database_summary(test_db, sample_quality_report):
    _, engine = test_db

    database.initialize_database()

    transactions = pd.DataFrame({
        "InvoiceNo": ["1001", "1002", "1003"],
        "Quantity": [1, 2, 3],
    })
    database.save_transactions(transactions)

    database.save_quality_report(sample_quality_report)

    summary = database.get_database_summary()

    assert summary["stored_transactions"] == 3
    assert summary["saved_quality_reports"] == 1


def test_save_investigation_returns_id(
    test_db,
    sample_investigation,
):
    database.initialize_investigation_history()

    investigation_id = database.save_investigation(
        sample_investigation
    )

    assert isinstance(investigation_id, int)
    assert investigation_id > 0


def test_get_investigation_history_returns_saved_report(
    test_db,
    sample_investigation,
):
    database.initialize_investigation_history()
    database.save_investigation(sample_investigation)

    history = database.get_investigation_history()

    assert len(history) == 1
    assert history[0]["summary"] == (
        "Customer ID completeness requires investigation."
    )
    assert history[0]["findings"][0]["title"] == (
        "Missing Customer IDs"
    )
    assert history[0]["limitations"] == [
        "The reason for missing IDs is unknown."
    ]


def test_investigation_history_is_newest_first(
    test_db,
    sample_investigation,
):
    database.initialize_investigation_history()

    first_report = sample_investigation.model_copy(
        update={"summary": "First investigation"}
    )
    second_report = sample_investigation.model_copy(
        update={"summary": "Second investigation"}
    )

    database.save_investigation(first_report)
    database.save_investigation(second_report)

    history = database.get_investigation_history()

    assert history[0]["summary"] == "Second investigation"
    assert history[1]["summary"] == "First investigation"


def test_history_limit_is_respected(
    test_db,
    sample_investigation,
):
    database.initialize_investigation_history()

    for number in range(3):
        report = sample_investigation.model_copy(
            update={"summary": f"Investigation {number}"}
        )
        database.save_investigation(report)

    history = database.get_investigation_history(limit=2)

    assert len(history) == 2
    assert history[0]["summary"] == "Investigation 2"


def test_empty_investigation_history_returns_empty_list(test_db):
    database.initialize_investigation_history()

    history = database.get_investigation_history()

    assert history == []


def test_get_historical_context(test_db, sample_investigation):
    database.initialize_investigation_history()
    database.save_investigation(sample_investigation)

    context = database.get_historical_context(limit=3)

    assert len(context) == 1
    assert context[0]["summary"] == (
        "Customer ID completeness requires investigation."
    )
    assert "investigation_id" in context[0]
    assert "timestamp" in context[0]
    assert "findings" in context[0]
    assert "limitations" in context[0]


def test_empty_historical_context_returns_empty_list(test_db):
    database.initialize_investigation_history()

    context = database.get_historical_context()

    assert context == []


def test_database_operations_do_not_use_production_database(
    test_db,
    sample_investigation,
):
    database_path, _ = test_db

    database.initialize_investigation_history()
    database.save_investigation(sample_investigation)

    assert database_path.exists()
    assert database_path.name == "test_dataguard.db"
    assert database_path != database.PROJECT_ROOT / "data" / "dataguard.db"

