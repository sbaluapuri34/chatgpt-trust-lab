from __future__ import annotations

import httpx
import pytest

from phase3.config import Phase3Config
from phase3.db import get_db_connection
from phase3.deep_analysis import run_deep_analysis
from phase3.json_parse import extract_json_array
from phase3.llm import GeminiClient, GroqClient, build_llm_clients
from phase3.relevance import run_relevance
from phase3.themes import is_valid_theme
from phase3.validation import validate_deep_result


pytestmark = pytest.mark.integration


@pytest.fixture
def require_groq(has_groq_key: bool) -> None:
    if not has_groq_key:
        pytest.skip("GROQ_API_KEY not set in .env")


@pytest.fixture
def require_gemini(has_gemini_key: bool) -> None:
    if not has_gemini_key:
        pytest.skip("GEMINI_API_KEY not set in .env")


def test_api_keys_configured(phase3_config: Phase3Config, require_groq: None, require_gemini: None) -> None:
    assert phase3_config.llm.primary == "groq"
    assert phase3_config.groq_api_key
    assert phase3_config.gemini_api_key


def test_groq_client_smoke(phase3_config: Phase3Config, require_groq: None) -> None:
    client = GroqClient(phase3_config.groq_api_key, phase3_config.llm.groq, timeout=60.0)
    reply = client.complete(
        system_prompt="Reply with JSON only: {\"ok\": true}",
        user_prompt='Return exactly: [{"id":"test","relevant":true,"relevance_score":1.0,"reason":"ok"}]',
    )
    parsed = extract_json_array(reply)
    assert parsed[0]["id"] == "test"


def test_gemini_client_smoke(phase3_config: Phase3Config, require_gemini: None) -> None:
    client = GeminiClient(phase3_config.gemini_api_key, phase3_config.llm.gemini, timeout=60.0)
    try:
        reply = client.complete(
            system_prompt="Reply with JSON only.",
            user_prompt='Return exactly: [{"id":"test","relevant":true,"relevance_score":1.0,"reason":"ok"}]',
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            pytest.skip("Gemini rate limited (429) — fallback client configured but quota busy")
        raise
    parsed = extract_json_array(reply)
    assert parsed[0]["relevant"] is True


def test_live_relevance_stage(phase3_config: Phase3Config, require_groq: None) -> None:
    summary = run_relevance(config=phase3_config, force=True, use_mock=False)
    assert summary["posts_processed"] == 2

    conn = get_db_connection(phase3_config.db_path)
    rows = conn.execute(
        """
        SELECT post_id, stage1_relevant, stage1_relevance_score, stage1_reason, stage1_model
        FROM post_analysis ORDER BY post_id
        """
    ).fetchall()
    conn.close()

    assert len(rows) == 2
    by_id = {row["post_id"]: row for row in rows}
    assert by_id["post_high"]["stage1_model"] == "groq"
    assert by_id["post_high"]["stage1_relevant"] == 1
    assert by_id["post_high"]["stage1_reason"]
    assert 0.0 <= by_id["post_high"]["stage1_relevance_score"] <= 1.0


def test_live_deep_analysis_stage(phase3_config: Phase3Config, require_groq: None) -> None:
    run_relevance(config=phase3_config, force=True, use_mock=False)
    summary = run_deep_analysis(config=phase3_config, force=True, use_mock=False)
    assert summary["posts_processed"] >= 1

    conn = get_db_connection(phase3_config.db_path)
    row = conn.execute(
        """
        SELECT primary_theme, secondary_themes, theme_rationale, evidence_quote,
               severity, model_confidence, stage2_model
        FROM post_analysis WHERE post_id = 'post_high'
        """
    ).fetchone()
    text = conn.execute("SELECT text FROM posts WHERE id = 'post_high'").fetchone()["text"]
    conn.close()

    assert row is not None
    assert row["stage2_model"] == "groq"
    assert is_valid_theme(row["primary_theme"])
    assert row["theme_rationale"]
    assert row["evidence_quote"] in text
    assert row["severity"] in ("low", "medium", "high")
    assert 0.0 <= row["model_confidence"] <= 1.0

    validate_deep_result(
        {
            "id": "post_high",
            "primary_theme": row["primary_theme"],
            "secondary_themes": [],
            "theme_rationale": row["theme_rationale"],
            "evidence_quote": row["evidence_quote"],
            "severity": row["severity"],
            "model_confidence": row["model_confidence"],
        },
        post_texts={"post_high": text},
    )


def test_live_full_pipeline(phase3_config: Phase3Config, require_groq: None) -> None:
    """End-to-end: mock-free relevance + deep on fixture candidates."""
    run_relevance(config=phase3_config, force=True, use_mock=False)
    run_deep_analysis(config=phase3_config, force=True, use_mock=False)

    conn = get_db_connection(phase3_config.db_path)
    themed = conn.execute(
        "SELECT COUNT(*) AS n FROM post_analysis WHERE primary_theme IS NOT NULL"
    ).fetchone()["n"]
    conn.close()
    assert themed >= 1


def test_llm_fallback_chain_includes_gemini(phase3_config: Phase3Config, require_groq: None, require_gemini: None) -> None:
    clients = build_llm_clients(
        stage="relevance",
        primary=phase3_config.llm.primary,
        fallback=phase3_config.llm.fallback,
        groq_api_key=phase3_config.groq_api_key,
        gemini_api_key=phase3_config.gemini_api_key,
        groq_config=phase3_config.llm.groq,
        gemini_config=phase3_config.llm.gemini,
        use_mock=False,
    )
    names = [c.name for c in clients]
    assert names[0] == "groq"
    assert "gemini" in names
