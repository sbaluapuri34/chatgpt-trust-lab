from __future__ import annotations

import logging
from pathlib import Path

from phase2.config import Phase2Config, load_phase2_config
from phase2.db import clear_post_features, get_connection, init_schema
from phase2.keywords import analyze_text

logger = logging.getLogger(__name__)


def preprocess_posts(
    *,
    db_path: Path | str | None = None,
    config: Phase2Config | None = None,
) -> dict[str, int]:
    """Compute keyword features for every post and store in ``post_features``."""
    cfg = config or load_phase2_config()
    database = Path(db_path) if db_path else cfg.db_path

    conn = get_connection(database)
    init_schema(conn)
    clear_post_features(conn)

    rows = conn.execute("SELECT id, text FROM posts ORDER BY id").fetchall()
    processed = 0

    for row in rows:
        text = str(row["text"])
        result = analyze_text(text, cfg.keyword_categories)

        conn.execute(
            """
            INSERT INTO post_features (
                post_id, text_length, keyword_match_count,
                match_confidence, match_hallucinations, match_trust,
                match_trust_loss, match_consequences, category_hit_count,
                is_candidate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                row["id"],
                len(text),
                result.keyword_match_count,
                result.match_confidence,
                result.match_hallucinations,
                result.match_trust,
                result.match_trust_loss,
                result.match_consequences,
                result.category_hit_count,
            ),
        )
        processed += 1

    conn.commit()
    conn.close()

    logger.info("Preprocessed %s posts in %s", processed, database)
    return {"posts_preprocessed": processed}
