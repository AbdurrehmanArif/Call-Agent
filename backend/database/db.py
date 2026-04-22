"""
Database operations for call logs.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from backend.utils.config import config


class Database:
    """SQLite database handler for call logs."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                caller_id TEXT,
                duration_seconds REAL,
                transcript TEXT,
                detected_intent TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                resolution_status TEXT,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogue_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES call_logs(session_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON call_logs(session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON call_logs(timestamp)
        """)

        conn.commit()
        conn.close()

    def log_call(
        self,
        session_id: str,
        caller_id: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        transcript: Optional[str] = None,
        detected_intent: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        sentiment_label: Optional[str] = None,
        resolution_status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """Log a call session."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO call_logs (
                session_id, caller_id, duration_seconds, transcript,
                detected_intent, sentiment_score, sentiment_label,
                resolution_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, caller_id, duration_seconds, transcript,
            detected_intent, sentiment_score, sentiment_label,
            resolution_status, notes
        ))

        call_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return call_id

    def add_dialogue_entry(
        self,
        session_id: str,
        role: str,
        message: str
    ) -> int:
        """Add a dialogue entry (user or assistant message)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO dialogue_history (session_id, role, message)
            VALUES (?, ?, ?)
        """, (session_id, role, message))

        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return entry_id

    def get_dialogue_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get dialogue history for a session."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT role, message, timestamp
            FROM dialogue_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {"role": row["role"], "message": row["message"], "timestamp": row["timestamp"]}
            for row in rows
        ]

    def get_call_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get call log by session ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM call_logs WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_recent_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent call logs."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM call_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_call_resolution(
        self,
        session_id: str,
        resolution_status: str,
        notes: Optional[str] = None
    ):
        """Update call resolution status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE call_logs
            SET resolution_status = ?, notes = ?
            WHERE session_id = ?
        """, (resolution_status, notes, session_id))

        conn.commit()
        conn.close()


# Singleton instance
db = Database()
