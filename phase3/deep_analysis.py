from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase3.config import Phase3Config, load_phase3_config
from phase3.db import get_db_connection
from phase3.payloads import load_full_text_map, load_stage1_relevant_posts
from phase3.pipeline import run_batches
from phase3.validation import labels_to_json, themes_to_json, validate_deep_batch

logger = logging.getLogger(__name__)


def persist_deep_results(conn: sqlite3.Connection, results: list[dict[str, Any]], *, model: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for row in results:
        conn.execute(
            """
            INSERT INTO post_analysis (
                post_id, primary_theme, secondary_themes, theme_rationale,
                evidence_quote, severity, model_confidence, secondary_labels,
                stage2_model, stage2_processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_id) DO UPDATE SET
                primary_theme = excluded.primary_theme,
                secondary_themes = excluded.secondary_themes,
                theme_rationale = excluded.theme_rationale,
                evidence_quote = excluded.evidence_quote,
                severity = excluded.severity,
                model_confidence = excluded.model_confidence,
                secondary_labels = excluded.secondary_labels,
                stage2_model = excluded.stage2_model,
                stage2_processed_at = excluded.stage2_processed_at
            """,
            (
                row["id"],
                row["primary_theme"],
                themes_to_json(row["secondary_themes"]),
                row["theme_rationale"],
                row["evidence_quote"],
                row["severity"],
                row["model_confidence"],
                labels_to_json(row["secondary_labels"]),
                model,
                now,
            ),
        )
    conn.commit()


def run_deep_analysis(
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
    posts = load_stage1_relevant_posts(
        conn,
        include_keyword_summary=include_kw,
        max_text_chars=cfg.llm.batching.max_text_chars,
    )
    logger.info("Stage 2: %s Stage-1-relevant posts", len(posts))
    full_texts = load_full_text_map(conn, [str(post["id"]) for post in posts])

    plan_path = cfg.batches_dir / "deep" / "batch_plan.json"

    def persist_fn(results: list[dict[str, Any]], *, model: str) -> None:
        persist_deep_results(conn, results, model=model)

    summary = run_batches(
        config=cfg,
        stage="deep",
        posts=posts,
        plan_path=plan_path,
        system_prompt_path=cfg.deep_prompt_path,
        reserved_output_tokens=cfg.llm.batching.reserved_output_tokens_deep,
        validate_fn=validate_deep_batch,
        persist_fn=persist_fn,
        force=force,
        use_mock=use_mock,
        validation_post_texts=full_texts,
    )
    conn.close()
    return summary
