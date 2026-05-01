import sqlite3
from contextlib import closing

from app.config import get_settings


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    conn = sqlite3.connect(str(settings.database_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute("PRAGMA table_info(tickets)")
        existing_columns = {row["name"] for row in cursor.fetchall()}

        if "priority" not in existing_columns:
            cursor.execute(
                "ALTER TABLE tickets ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'"
            )

        if "updated_at" not in existing_columns:
            cursor.execute(
                "ALTER TABLE tickets ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
            )
            cursor.execute(
                "UPDATE tickets SET updated_at = created_at WHERE updated_at IS NULL OR updated_at = ''"
            )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_status_created_at ON tickets(status, created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_priority_created_at ON tickets(priority, created_at DESC)"
        )
        conn.commit()


def check_database_health() -> bool:
    try:
        with closing(get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except sqlite3.Error:
        return False

