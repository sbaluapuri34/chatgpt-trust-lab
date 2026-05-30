from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,
    selftext TEXT NOT NULL,
    score INTEGER NOT NULL,
    created_utc REAL NOT NULL,
    url TEXT NOT NULL,
    text TEXT NOT NULL,
    weight REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS post_features (
    post_id TEXT PRIMARY KEY REFERENCES posts(id),
    text_length INTEGER NOT NULL,
    keyword_match_count INTEGER NOT NULL,
    match_confidence INTEGER NOT NULL,
    match_hallucinations INTEGER NOT NULL,
    match_trust INTEGER NOT NULL,
    match_trust_loss INTEGER NOT NULL,
    match_consequences INTEGER NOT NULL,
    category_hit_count INTEGER NOT NULL,
    relevance_raw REAL,
    rank_score REAL,
    is_candidate INTEGER NOT NULL DEFAULT 0
);
"""


def get_connection(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def clear_post_features(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM post_features")
    conn.commit()


def reset_candidates(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE post_features SET is_candidate = 0, relevance_raw = NULL, rank_score = NULL")
    conn.commit()
