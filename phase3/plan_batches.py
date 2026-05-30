from __future__ import annotations

import logging
from pathlib import Path

from phase3.batching import plan_batches, save_batch_plan
from phase3.config import Phase3Config, load_phase3_config
from phase3.db import get_db_connection
from phase3.payloads import load_candidate_posts, load_stage1_relevant_posts

logger = logging.getLogger(__name__)


def plan_relevance_batches(*, config: Phase3Config | None = None, db_path: Path | str | None = None) -> Path:
    cfg = config or load_phase3_config()
    database = Path(db_path) if db_path else cfg.db_path
    conn = get_db_connection(database)
    posts = load_candidate_posts(conn, include_keyword_summary=cfg.llm.batching.include_keyword_summary)
    conn.close()

    plan = plan_batches(
        posts,
        stage="relevance",
        batching=cfg.llm.batching,
        reserved_output_tokens=cfg.llm.batching.reserved_output_tokens_relevance,
    )
    path = cfg.batches_dir / "relevance" / "batch_plan.json"
    save_batch_plan(plan, path)
    logger.info("Relevance plan: %s batches, %s posts", len(plan.batches), len(posts))
    return path


def plan_deep_batches(*, config: Phase3Config | None = None, db_path: Path | str | None = None) -> Path:
    cfg = config or load_phase3_config()
    database = Path(db_path) if db_path else cfg.db_path
    conn = get_db_connection(database)
    posts = load_stage1_relevant_posts(conn, include_keyword_summary=cfg.llm.batching.include_keyword_summary)
    conn.close()

    plan = plan_batches(
        posts,
        stage="deep",
        batching=cfg.llm.batching,
        reserved_output_tokens=cfg.llm.batching.reserved_output_tokens_deep,
    )
    path = cfg.batches_dir / "deep" / "batch_plan.json"
    save_batch_plan(plan, path)
    logger.info("Deep plan: %s batches, %s posts", len(plan.batches), len(posts))
    return path
