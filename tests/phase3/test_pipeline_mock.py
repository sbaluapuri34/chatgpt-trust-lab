from __future__ import annotations

import json
from phase3.config import Phase3Config
from phase3.db import get_db_connection
from phase3.deep_analysis import run_deep_analysis
from phase3.relevance import run_relevance
from phase3.themes import is_valid_theme


def test_mock_full_phase3_pipeline(phase3_config: Phase3Config) -> None:
    rel = run_relevance(config=phase3_config, force=True, use_mock=True)
    assert rel["posts_processed"] == 2

    deep = run_deep_analysis(config=phase3_config, force=True, use_mock=True)
    assert deep["posts_processed"] >= 1

    conn = get_db_connection(phase3_config.db_path)
    high = conn.execute(
        "SELECT stage1_relevant, stage1_model, primary_theme, evidence_quote FROM post_analysis WHERE post_id = 'post_high'"
    ).fetchone()
    conn.close()

    assert high is not None
    assert high["stage1_relevant"] == 1
    assert high["stage1_model"] == "mock"
    assert is_valid_theme(high["primary_theme"])
    assert high["evidence_quote"]


def test_batch_cache_written(phase3_config: Phase3Config) -> None:
    run_relevance(config=phase3_config, force=True, use_mock=True)
    cache = phase3_config.batches_dir / "relevance" / "batch_001_results.json"
    assert cache.exists()
    data = json.loads(cache.read_text(encoding="utf-8"))
    assert data["model"] == "mock"
    assert len(data["results"]) == 2
