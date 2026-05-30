from __future__ import annotations

import json
import math
import sqlite3

from phase2.db import get_connection, init_schema
from phase2.ingest import compute_weight, ingest_raw_posts
from phase2.preprocess import preprocess_posts
from phase2.select_candidates import select_candidates


def test_compute_weight():
    assert compute_weight(0) == 0.0
    assert math.isclose(compute_weight(10), math.log(11))
    assert math.isclose(compute_weight(-5), math.log(1))


def test_full_phase2_pipeline(phase2_config, sample_raw_path, tmp_path):
    cfg = phase2_config
    ingest_summary = ingest_raw_posts(raw_path=sample_raw_path, db_path=cfg.db_path, config=cfg)
    assert ingest_summary["posts_ingested"] == 4

    preprocess_summary = preprocess_posts(db_path=cfg.db_path, config=cfg)
    assert preprocess_summary["posts_preprocessed"] == 4

    report = select_candidates(db_path=cfg.db_path, config=cfg)
    assert report["N_raw"] == 4
    assert report["N_candidates"] == 2
    assert report["N_eligible"] == 2
    assert report["candidate_keyword_coverage_pct"] == 100.0

    conn = get_connection(cfg.db_path)
    init_schema(conn)

    high = conn.execute(
        """
        SELECT p.score, p.weight, f.keyword_match_count, f.is_candidate, f.rank_score
        FROM posts p
        JOIN post_features f ON f.post_id = p.id
        WHERE p.id = 'post_high'
        """
    ).fetchone()
    zero = conn.execute(
        "SELECT f.is_candidate, f.rank_score FROM post_features f WHERE f.post_id = 'post_zero'"
    ).fetchone()
    conn.close()

    assert high["is_candidate"] == 1
    assert high["keyword_match_count"] >= 6
    assert high["rank_score"] is not None
    assert zero["is_candidate"] == 0
    assert zero["rank_score"] is None

    report_path = cfg.aggregated_dir / "candidate_selection_report.json"
    assert report_path.exists()
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved["N_candidates"] == 2


def test_candidate_ranking_order(phase2_config, sample_raw_path):
    cfg = phase2_config
    ingest_raw_posts(raw_path=sample_raw_path, db_path=cfg.db_path, config=cfg)
    preprocess_posts(db_path=cfg.db_path, config=cfg)
    select_candidates(db_path=cfg.db_path, config=cfg)

    conn = get_connection(cfg.db_path)
    rows = conn.execute(
        """
        SELECT p.id, f.rank_score
        FROM post_features f
        JOIN posts p ON p.id = f.post_id
        WHERE f.is_candidate = 1
        ORDER BY f.rank_score DESC
        """
    ).fetchall()
    conn.close()

    ids = [row["id"] for row in rows]
    assert ids[0] == "post_high"
    assert set(ids) == {"post_high", "post_mid"}
