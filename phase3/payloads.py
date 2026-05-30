from __future__ import annotations

import json
import sqlite3
from typing import Any


def keyword_summary_from_row(row: sqlite3.Row) -> dict[str, int]:
    return {
        "keyword_match_count": int(row["keyword_match_count"]),
        "match_confidence": int(row["match_confidence"]),
        "match_hallucinations": int(row["match_hallucinations"]),
        "match_trust": int(row["match_trust"]),
        "match_trust_loss": int(row["match_trust_loss"]),
        "match_consequences": int(row["match_consequences"]),
        "category_hit_count": int(row["category_hit_count"]),
    }


_TRUNCATION_NOTE = (
    "\n\n[... post truncated for LLM context limit; assign themes from this excerpt ...]"
)


def truncate_text_for_llm(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars] + _TRUNCATION_NOTE


def build_post_payload(
    row: sqlite3.Row,
    *,
    include_keyword_summary: bool,
    max_text_chars: int | None = None,
) -> dict[str, Any]:
    text = str(row["text"])
    if max_text_chars is not None:
        text = truncate_text_for_llm(text, max_text_chars)
    payload: dict[str, Any] = {
        "id": row["id"],
        "text": text,
        "score": int(row["score"]),
    }
    if include_keyword_summary and row["keyword_match_count"] is not None:
        payload["keyword_summary"] = keyword_summary_from_row(row)
    return payload


def load_candidate_posts(
    conn: sqlite3.Connection,
    *,
    include_keyword_summary: bool,
    max_text_chars: int | None = None,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            p.id, p.text, p.score,
            f.keyword_match_count, f.match_confidence, f.match_hallucinations,
            f.match_trust, f.match_trust_loss, f.match_consequences, f.category_hit_count
        FROM posts p
        JOIN post_features f ON f.post_id = p.id
        WHERE f.is_candidate = 1
        ORDER BY p.id
        """
    ).fetchall()
    return [
        build_post_payload(row, include_keyword_summary=include_keyword_summary, max_text_chars=max_text_chars)
        for row in rows
    ]


def load_stage1_relevant_posts(
    conn: sqlite3.Connection,
    *,
    include_keyword_summary: bool,
    max_text_chars: int | None = None,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            p.id, p.text, p.score,
            f.keyword_match_count, f.match_confidence, f.match_hallucinations,
            f.match_trust, f.match_trust_loss, f.match_consequences, f.category_hit_count
        FROM posts p
        JOIN post_features f ON f.post_id = p.id
        JOIN post_analysis a ON a.post_id = p.id
        WHERE a.stage1_relevant = 1
        ORDER BY p.id
        """
    ).fetchall()
    return [
        build_post_payload(row, include_keyword_summary=include_keyword_summary, max_text_chars=max_text_chars)
        for row in rows
    ]


def posts_to_text_map(posts: list[dict[str, Any]]) -> dict[str, str]:
    return {str(post["id"]): str(post["text"]) for post in posts}


def load_full_text_map(conn: sqlite3.Connection, post_ids: list[str]) -> dict[str, str]:
    if not post_ids:
        return {}
    placeholders = ",".join("?" for _ in post_ids)
    rows = conn.execute(
        f"SELECT id, text FROM posts WHERE id IN ({placeholders})",
        post_ids,
    ).fetchall()
    return {str(row["id"]): str(row["text"]) for row in rows}


def serialize_posts_for_prompt(posts: list[dict[str, Any]]) -> str:
    return json.dumps(posts, ensure_ascii=False, indent=2)
