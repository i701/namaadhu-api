import sqlite3
import os
from typing import Optional, Dict
from contextlib import contextmanager


# Ensure data directory exists
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "prayer_times_cache.db")


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prayer_times_cache (
                date_key TEXT PRIMARY KEY,
                fajr TEXT NOT NULL,
                dhuhr TEXT NOT NULL,
                asr TEXT NOT NULL,
                maghrib TEXT NOT NULL,
                isha TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()


def get_cached_prayer_times(date_key: str) -> Optional[Dict[str, str]]:
    """
    Retrieve cached prayer times for a given date.

    Args:
        date_key: Date in YYYY-MM-DD format

    Returns:
        Dictionary with prayer times if found, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT fajr, dhuhr, asr, maghrib, isha
            FROM prayer_times_cache
            WHERE date_key = ?
        """,
            (date_key,),
        )
        row = cursor.fetchone()

        if row:
            return {
                "fajr": row["fajr"],
                "dhuhr": row["dhuhr"],
                "asr": row["asr"],
                "maghrib": row["maghrib"],
                "isha": row["isha"],
            }
        return None


def save_prayer_times(date_key: str, prayer_times: Dict[str, str]):
    """
    Save prayer times to cache.

    Args:
        date_key: Date in YYYY-MM-DD format
        prayer_times: Dictionary containing prayer times
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO prayer_times_cache
            (date_key, fajr, dhuhr, asr, maghrib, isha)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                date_key,
                prayer_times["fajr"],
                prayer_times["dhuhr"],
                prayer_times["asr"],
                prayer_times["maghrib"],
                prayer_times["isha"],
            ),
        )
        conn.commit()
