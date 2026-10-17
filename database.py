
import json
import sqlite3
from pathlib import Path

from models import CaseFile


DB_PATH = Path(__file__).parent / "crisis_intake.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the cases table if it doesn't exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                case_data TEXT NOT NULL
            )
            """
        )


def save_case(case: CaseFile) -> int:
    """Save a case and return its database ID."""

    case_json = case.model_dump_json()

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO cases (case_data) VALUES (?)",
            (case_json,),
        )
        case_id = cursor.lastrowid

    return case_id


def get_case(case_id: int) -> dict | None:
    """Retrieve one case by ID."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, created_at, case_data FROM cases WHERE id = ?",
            (case_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "case": json.loads(row["case_data"]),
    }


def list_cases(limit: int = 20) -> list[dict]:
    """Retrieve the most recently saved cases."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, case_data
            FROM cases
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "case": json.loads(row["case_data"]),
        }
        for row in rows
    ]
