from __future__ import annotations

import sqlite3
from pathlib import Path

from phase2.db import get_connection, init_schema as init_phase2_schema

PHASE3_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS post_analysis (
    post_id TEXT PRIMARY KEY REFERENCES posts(id),
    stage1_relevant INTEGER,
    stage1_relevance_score REAL,
    stage1_reason TEXT,
    stage1_model TEXT,
    stage1_processed_at TEXT,
    primary_theme TEXT,
    secondary_themes TEXT,
    theme_rationale TEXT,
    evidence_quote TEXT,
    severity TEXT,
    model_confidence REAL,
    secondary_labels TEXT,
    stage2_model TEXT,
    stage2_processed_at TEXT
);
"""


def init_phase3_schema(conn: sqlite3.Connection) -> None:
    init_phase2_schema(conn)
    conn.executescript(PHASE3_SCHEMA_SQL)
    conn.commit()


def get_db_connection(db_path: Path | str) -> sqlite3.Connection:
    conn = get_connection(db_path)
    init_phase3_schema(conn)
    return conn
