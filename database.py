"""
AgriSense Database Management Service
======================================
SQLite Persistence Layer adhering to PRD Section 12 & Specification Lock v1.1.

Schema:
  events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    zone1 REAL NOT NULL,
    zone2 REAL NOT NULL,
    tank REAL NOT NULL,
    rain INTEGER NOT NULL,
    manual INTEGER NOT NULL,
    pump INTEGER NOT NULL,
    active_zone TEXT NOT NULL,
    fsm_state TEXT NOT NULL,
    counter INTEGER NOT NULL,
    alarm INTEGER NOT NULL,
    message TEXT NOT NULL
  )

Guarantees:
- Parameterized SQL queries preventing injection.
- Context-manager connection lifecycle.
- Graceful empty-state handling (returns empty DataFrame with schema preserved, never crashes).
- Explicit clear_all_history() operation separated completely from simulation reset.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, List, Dict, Any, Optional
import pandas as pd

from digital_core import StepSnapshot


DEFAULT_DB_PATH = "agrisense.db"

EVENT_COLUMNS = [
    "id",
    "timestamp",
    "zone1",
    "zone2",
    "tank",
    "rain",
    "manual",
    "pump",
    "active_zone",
    "fsm_state",
    "counter",
    "alarm",
    "message",
]


class DatabaseManager:
    """Manages SQLite event persistence and analytics queries."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a managed SQLite connection with WAL mode and foreign keys enabled."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initializes the database schema if tables do not exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            zone1 REAL NOT NULL,
            zone2 REAL NOT NULL,
            tank REAL NOT NULL,
            rain INTEGER NOT NULL,
            manual INTEGER NOT NULL,
            pump INTEGER NOT NULL,
            active_zone TEXT NOT NULL,
            fsm_state TEXT NOT NULL,
            counter INTEGER NOT NULL,
            alarm INTEGER NOT NULL,
            message TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_fsm ON events(fsm_state);
        """
        with self.get_connection() as conn:
            conn.executescript(create_table_sql)

    def log_event(self, snapshot: StepSnapshot, timestamp: Optional[str] = None) -> int:
        """
        Records a simulation clock-step event in SQLite.
        Returns the inserted row ID.
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        sql = """
        INSERT INTO events (
            timestamp, zone1, zone2, tank, rain, manual, pump,
            active_zone, fsm_state, counter, alarm, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            ts,
            float(snapshot.zone1_moisture),
            float(snapshot.zone2_moisture),
            float(snapshot.tank_level),
            int(snapshot.rain_detected),
            int(snapshot.manual_override),
            int(snapshot.pump_output),
            snapshot.active_zone.value if hasattr(snapshot.active_zone, "value") else str(snapshot.active_zone),
            snapshot.fsm_state.value if hasattr(snapshot.fsm_state, "value") else str(snapshot.fsm_state),
            int(snapshot.counter),
            int(snapshot.alarm_output),
            str(snapshot.message),
        )
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.lastrowid or 0

    def fetch_events(self, limit: Optional[int] = None, ascending: bool = True) -> pd.DataFrame:
        """
        Fetches event records as a Pandas DataFrame.
        Gracefully returns an empty DataFrame with valid column names if the table is empty.
        """
        order = "ASC" if ascending else "DESC"
        sql = f"SELECT * FROM events ORDER BY id {order}"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"

        with self.get_connection() as conn:
            df = pd.read_sql_query(sql, conn)

        if df.empty:
            return pd.DataFrame(columns=EVENT_COLUMNS)
        return df

    def fetch_summary_metrics(self) -> Dict[str, int]:
        """
        Aggregates operational metrics across all historical events.
        Handles empty databases gracefully by returning 0s.
        """
        sql = """
        SELECT
            COUNT(*) AS total_events,
            COALESCE(SUM(CASE WHEN pump = 1 THEN 1 ELSE 0 END), 0) AS pump_active_events,
            COALESCE(SUM(CASE WHEN fsm_state = 'FAULT_LOCK' OR alarm = 1 THEN 1 ELSE 0 END), 0) AS fault_events,
            COALESCE(SUM(CASE WHEN rain = 1 THEN 1 ELSE 0 END), 0) AS rain_events,
            COALESCE(SUM(CASE WHEN counter = 4 AND pump = 1 THEN 1 ELSE 0 END), 0) AS fertigation_events
        FROM events;
        """
        with self.get_connection() as conn:
            cursor = conn.execute(sql)
            row = cursor.fetchone()
            if row:
                return {
                    "total_events": int(row["total_events"]),
                    "pump_active_events": int(row["pump_active_events"]),
                    "fault_events": int(row["fault_events"]),
                    "rain_events": int(row["rain_events"]),
                    "fertigation_events": int(row["fertigation_events"]),
                }
        return {
            "total_events": 0,
            "pump_active_events": 0,
            "fault_events": 0,
            "rain_events": 0,
            "fertigation_events": 0,
        }

    def clear_all_history(self) -> None:
        """
        Explicit administrative operation to purge all historical events.
        MUST NOT be called automatically during simulation reset.
        """
        with self.get_connection() as conn:
            conn.execute("DELETE FROM events;")
            conn.execute("DELETE FROM sqlite_sequence WHERE name='events';")


# Default global instance
default_db = DatabaseManager()
