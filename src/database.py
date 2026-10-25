
import json
import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "dataguard.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL)


def initialize_database() -> None:
    """Create the database tables if they do not exist."""

    with engine.begin() as connection:

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS quality_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp TEXT NOT NULL,
                total_rows INTEGER NOT NULL,
                total_columns INTEGER NOT NULL,
                duplicate_rows INTEGER NOT NULL,
                missing_cells INTEGER NOT NULL,
                completeness_score REAL NOT NULL,
                total_issues INTEGER NOT NULL,
                report_json TEXT NOT NULL
            )
        """))

def initialize_investigation_history():
    """Create the table used to store AI investigation reports."""

    connection = sqlite3.connect(DATABASE_PATH )

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investigation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp TEXT NOT NULL,
                summary TEXT NOT NULL,
                findings_json TEXT NOT NULL,
                limitations_json TEXT NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()



def save_transactions(data: pd.DataFrame) -> None:
    """Save processed transactions to SQLite."""

    data.to_sql(
        name="retail_transactions",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=10_000,
    )

    print(
        f"Saved {len(data):,} processed records "
        "to retail_transactions."
    )


def save_quality_report(report: dict) -> None:
    """Persist one quality report for each pipeline run."""

    initialize_database()

    report_json = json.dumps(
        report,
        default=str,
    )

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO quality_reports (
                    run_timestamp,
                    total_rows,
                    total_columns,
                    duplicate_rows,
                    missing_cells,
                    completeness_score,
                    total_issues,
                    report_json
                )
                VALUES (
                    datetime('now'),
                    :total_rows,
                    :total_columns,
                    :duplicate_rows,
                    :missing_cells,
                    :completeness_score,
                    :total_issues,
                    :report_json
                )
            """),
            {
                "total_rows": report["total_rows"],
                "total_columns": report["total_columns"],
                "duplicate_rows": report["duplicate_rows"],
                "missing_cells": report["missing_cells"],
                "completeness_score": report["completeness_score"],
                "total_issues": report["total_issues"],
                "report_json": report_json,
            },
        )

    print("Quality report saved to quality_reports.")


def get_database_summary() -> dict:
    """Return basic database statistics."""

    with engine.connect() as connection:

        transaction_count = connection.execute(
            text("SELECT COUNT(*) FROM retail_transactions")
        ).scalar_one()

        report_count = connection.execute(
            text("SELECT COUNT(*) FROM quality_reports")
        ).scalar_one()

    return {
        "stored_transactions": transaction_count,
        "saved_quality_reports": report_count,
    }

def save_investigation(report):
    """Save a validated AI investigation report to SQLite."""

    import json
    from datetime import datetime, timezone

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO investigation_history (
                run_timestamp,
                summary,
                findings_json,
                limitations_json
            )
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            report.summary,
            json.dumps(
                [finding.model_dump() for finding in report.findings],
                ensure_ascii=False
            ),
            json.dumps(report.limitations, ensure_ascii=False)
        ))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()



def get_investigation_history(limit=10):
    """Retrieve the most recent AI investigation reports."""

    import json
    import sqlite3

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                run_timestamp,
                summary,
                findings_json,
                limitations_json
            FROM investigation_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        history = []

        for row in rows:
            history.append({
                "id": row["id"],
                "run_timestamp": row["run_timestamp"],
                "summary": row["summary"],
                "findings": json.loads(row["findings_json"]),
                "limitations": json.loads(row["limitations_json"])
            })

        return history

    finally:
        connection.close()


def get_historical_context(limit=3):
    """Retrieve recent investigations as context for the AI."""

    history = get_investigation_history(limit=limit)

    if not history:
        return []

    historical_context = []

    for report in history:
        historical_context.append({
            "investigation_id": report["id"],
            "timestamp": report["run_timestamp"],
            "summary": report["summary"],
            "findings": report["findings"],
            "limitations": report["limitations"],
        })

    return historical_context

