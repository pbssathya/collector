"""
SQLite implementation of the Knowledge Store.
"""

import json
import sqlite3
from typing import Optional, List, Any
from datetime import datetime
from pathlib import Path

from .knowledge_store import KnowledgeRecord, KnowledgeStore


class SQLiteKnowledgeStore(KnowledgeStore):
    """SQLite implementation of the Knowledge Store."""

    def __init__(self, db_path: str = "knowledge.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                raw_data TEXT NOT NULL,
                parsed_data TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source ON records(source)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_collected_at ON records(collected_at)
        """)

        conn.commit()
        conn.close()

    def save(self, record: KnowledgeRecord) -> str:
        """Save a KnowledgeRecord and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Serialize data
        raw_json = json.dumps(record.raw_data, default=str)
        parsed_json = json.dumps(record.parsed_data, default=str) if record.parsed_data else None
        metadata_json = json.dumps(record.metadata, default=str) if record.metadata else "{}"

        cursor.execute("""
            INSERT INTO records (
                source, collected_at, raw_data, parsed_data, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record.source,
            record.collected_at.isoformat(),
            raw_json,
            parsed_json,
            metadata_json,
            datetime.now().isoformat(),
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return str(record_id)

    def get(self, record_id: str) -> Optional[KnowledgeRecord]:
        """Retrieve a KnowledgeRecord by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, source, collected_at, raw_data, parsed_data, metadata
            FROM records WHERE id = ?
        """, (record_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_record(row)

    def query(self, source: Optional[str] = None, limit: int = 100) -> List[KnowledgeRecord]:
        """Query records by source."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if source:
            cursor.execute("""
                SELECT id, source, collected_at, raw_data, parsed_data, metadata
                FROM records WHERE source = ?
                ORDER BY collected_at DESC
                LIMIT ?
            """, (source, limit))
        else:
            cursor.execute("""
                SELECT id, source, collected_at, raw_data, parsed_data, metadata
                FROM records
                ORDER BY collected_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_record(row) for row in rows]

    def count(self) -> int:
        """Return the total number of records."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def _row_to_record(self, row) -> KnowledgeRecord:
        """Convert a database row to a KnowledgeRecord."""
        record_id, source, collected_at, raw_data, parsed_data, metadata = row

        record = KnowledgeRecord(
            source=source,
            collected_at=datetime.fromisoformat(collected_at),
            raw_data=json.loads(raw_data),
            parsed_data=json.loads(parsed_data) if parsed_data else None,
            metadata=json.loads(metadata) if metadata else {},
        )
        record.id = str(record_id)
        return record
