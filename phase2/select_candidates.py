from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from phase2.config import Phase2Config, load_phase2_config
from phase2.db import get_connection, init_schema, reset_candidates

logger = logging.getLogger(__name__)


def min_max_normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high == low:
        return [1.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def select_candidates(
    *,
    db_path: Path | str | None = None,
    config: Phase2Config | None = None,
    report_path: Path | str | None = None,
) -> dict[str, object]:
    """Rank posts and mark top-K candidates for Phase 3 LLM stages."""
    cfg = config or load_phase2_config()
    database = Path(db_path) if db_path else cfg.db_path
    report_file = (
        Path(report_path)
        if report_path
        else cfg.aggregated_dir / "candidate_selection_report.json"
    )

    conn = get_connection(database)
    init_schema(conn)
    reset_candidates(conn)

    rows = conn.execute(
        """
        SELECT
            p.id,
            p.score,
            f.keyword_match_count,
            f.category_hit_count
        FROM posts p
        JOIN post_features f ON f.post_id = p.id
        ORDER BY p.id
        """
    ).fetchall()

    if not rows:
        conn.close()
        raise RuntimeError("No posts with features found. Run preprocess first.")

    sel = cfg.selection
    relevance_values: list[float] = []
    score_values: list[float] = []
    eligible_indices: list[int] = []

    for index, row in enumerate(rows):
        keyword_hits = int(row["keyword_match_count"])
        category_hits = int(row["category_hit_count"])
        relevance = keyword_hits + sel.category_weight * category_hits
        relevance_values.append(float(relevance))
        score_values.append(float(row["score"]))

        if keyword_hits >= sel.require_min_keyword_matches:
            eligible_indices.append(index)

    norm_relevance = min_max_normalize(relevance_values)
    norm_score = min_max_normalize(score_values)

    ranked: list[tuple[str, float, float]] = []
    for index in eligible_indices:
        row = rows[index]
        rank_score = sel.w_keyword * norm_relevance[index] + sel.w_score * norm_score[index]
        ranked.append((str(row["id"]), relevance_values[index], rank_score))

    ranked.sort(key=lambda item: (-item[2], -item[1], item[0]))
    k = min(sel.max_candidates, len(ranked))
    candidate_ids = {post_id for post_id, _, _ in ranked[:k]}

    for post_id, relevance_raw, rank_score in ranked:
        conn.execute(
            """
            UPDATE post_features
            SET relevance_raw = ?, rank_score = ?, is_candidate = ?
            WHERE post_id = ?
            """,
            (relevance_raw, rank_score, 1 if post_id in candidate_ids else 0, post_id),
        )

    # Posts below min keyword threshold keep NULL rank fields and is_candidate=0.
    conn.commit()

    total_posts = len(rows)
    n_candidates = len(candidate_ids)
    n_eligible = len(eligible_indices)
    n_with_keywords = sum(1 for row in rows if int(row["keyword_match_count"]) >= 1)
    keyword_coverage = (n_with_keywords / total_posts) if total_posts else 0.0
    candidate_keyword_hits = conn.execute(
        """
        SELECT COUNT(*) FROM post_features
        WHERE is_candidate = 1 AND keyword_match_count >= 1
        """
    ).fetchone()[0]
    candidate_keyword_pct = (candidate_keyword_hits / n_candidates) if n_candidates else 0.0

    report: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "N_raw": total_posts,
        "N_eligible": n_eligible,
        "N_candidates": n_candidates,
        "K": sel.max_candidates,
        "weights": {
            "w_keyword": sel.w_keyword,
            "w_score": sel.w_score,
            "category_weight": sel.category_weight,
        },
        "require_min_keyword_matches": sel.require_min_keyword_matches,
        "normalization": "min_max",
        "keyword_match_counting": "per_occurrence_case_insensitive_substring",
        "posts_with_any_keyword": n_with_keywords,
        "candidate_keyword_coverage_pct": round(candidate_keyword_pct * 100, 2),
        "corpus_keyword_coverage_pct": round(keyword_coverage * 100, 2),
    }

    report_file.parent.mkdir(parents=True, exist_ok=True)
    with report_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    conn.close()
    logger.info(
        "Selected %s candidates from %s posts (%s eligible)",
        n_candidates,
        total_posts,
        n_eligible,
    )
    return report
