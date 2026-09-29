import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "meetings.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at TEXT NOT NULL,
                transcript TEXT, language TEXT, duration REAL, analysis_json TEXT
            )
        """)


def create_meeting(meeting_id: str, filename: str) -> None:
    with _connect() as conn:
        conn.execute("INSERT OR REPLACE INTO meetings (id, filename, created_at) VALUES (?, ?, ?)",
                     (meeting_id, filename, datetime.now(timezone.utc).isoformat()))


def save_transcript(meeting_id: str, transcript: str, language: str, duration: float) -> None:
    with _connect() as conn:
        conn.execute("UPDATE meetings SET transcript = ?, language = ?, duration = ? WHERE id = ?",
                     (transcript, language, duration, meeting_id))


def save_analysis(meeting_id: str, analysis: dict) -> None:
    with _connect() as conn:
        conn.execute("UPDATE meetings SET analysis_json = ? WHERE id = ?",
                     (json.dumps(analysis, ensure_ascii=False), meeting_id))


def list_meetings() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT id, filename, created_at, language, duration, transcript, analysis_json FROM meetings ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(row) for row in rows]


def get_meeting(meeting_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    return _row_to_dict(row) if row else None


def delete_meeting(meeting_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        return cursor.rowcount > 0


def clear_meetings() -> int:
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
        conn.execute("DELETE FROM meetings")
        return count


def _row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    analysis_json = data.pop("analysis_json", None)
    data["analysis"] = json.loads(analysis_json) if analysis_json else None
    data["transcribed"] = bool(data.get("transcript"))
    return data
