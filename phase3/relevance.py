from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase3.config import Phase3Config, load_phase3_config
from phase3.db import get_db_connection
from phase3.payloads import load_candidate_posts, load_full_text_map
from phase3.pipeline import run_batches
from phase3.validation import validate_relevance_batch

logger = logging.getLogger(__name__)


def persist_relevance_results(conn: sqlite3.Connection, results: list[dict[str, Any]], *, model: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for row in results:
        conn.execute(
            """
            INSERT INTO post_analysis (
                post_id, stage1_relevant, stage1_relevance_score, stage1_reason,
                stage1_model, stage1_processed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_id) DO UPDATE SET
                stage1_relevant = excluded.stage1_relevant,
                stage1_relevance_score = excluded.stage1_relevance_score,
                stage1_reason = excluded.stage1_reason,
                stage1_model = excluded.stage1_model,
                stage1_processed_at = excluded.stage1_processed_at
            """,
            (
                row["id"],
                1 if row["relevant"] else 0,
                row["relevance_score"],
                row["reason"],
                model,
                now,
            ),
        )
    conn.commit()


def run_relevance(
    *,
    config: Phase3Config | None = None,
    db_path: Path | str | None = None,
    force: bool = False,
    use_mock: bool = False,
) -> dict[str, int]:
    cfg = config or load_phase3_config()
    database = Path(db_path) if db_path else cfg.db_path
    conn = get_db_connection(database)

    include_kw = cfg.llm.batching.include_keyword_summary
    posts = load_candidate_posts(
        conn,
        include_keyword_summary=include_kw,
        max_text_chars=cfg.llm.batching.max_text_chars,
    )
    logger.info("Stage 1: %s candidate posts", len(posts))
    full_texts = load_full_text_map(conn, [str(post["id"]) for post in posts])

    plan_path = cfg.batches_dir / "relevance" / "batch_plan.json"

    def persist_fn(results: list[dict[str, Any]], *, model: str) -> None:
        persist_relevance_results(conn, results, model=model)

    summary = run_batches(
        config=cfg,
        stage="relevance",
        posts=posts,
        plan_path=plan_path,
        system_prompt_path=cfg.relevance_prompt_path,
        reserved_output_tokens=cfg.llm.batching.reserved_output_tokens_relevance,
        validate_fn=validate_relevance_batch,
        persist_fn=persist_fn,
        force=force,
        use_mock=use_mock,
        validation_post_texts=full_texts,
    )
    conn.close()
    return summary
