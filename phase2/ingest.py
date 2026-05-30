from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

from phase1.collector import combined_text
from phase2.config import Phase2Config, load_phase2_config
from phase2.db import get_connection, init_schema
from project.checkpoint import resolve_raw_posts_path

logger = logging.getLogger(__name__)


def compute_weight(score: int) -> float:
    return math.log(1 + max(score, 0))


def find_latest_raw_file(raw_dir: Path) -> Path:
    candidates = sorted(raw_dir.glob("posts_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No posts_*.json files found in {raw_dir}")
    return candidates[0]


def load_raw_posts(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in {path}")
    return data


def ingest_raw_posts(
    *,
    raw_path: Path | str | None = None,
    db_path: Path | str | None = None,
    config: Phase2Config | None = None,
    replace_existing: bool = True,
) -> dict[str, Any]:
    """Load raw JSON posts into SQLite ``posts`` table."""
    cfg = config or load_phase2_config()
    source = resolve_raw_posts_path(cfg.raw_dir, explicit_path=raw_path)
    database = Path(db_path) if db_path else cfg.db_path

    posts = load_raw_posts(source)
    conn = get_connection(database)
    init_schema(conn)

    if replace_existing:
        conn.execute("DELETE FROM post_features")
        conn.execute("DELETE FROM posts")

    inserted = 0
    for row in posts:
        post_id = str(row["id"])
        title = str(row.get("title", ""))
        selftext = str(row.get("selftext", ""))
        text = combined_text(title, selftext)
        score = int(row.get("score", 0))

        conn.execute(
            """
            INSERT OR REPLACE INTO posts (
                id, subreddit, title, selftext, score, created_utc, url, text, weight
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_id,
                str(row.get("subreddit", "")),
                title,
                selftext,
                score,
                float(row.get("created_utc", 0)),
                str(row.get("url", "")),
                text,
                compute_weight(score),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()

    summary = {
        "source_file": str(source),
        "db_path": str(database),
        "posts_ingested": inserted,
    }
    logger.info("Ingested %s posts from %s into %s", inserted, source, database)
    return summary
