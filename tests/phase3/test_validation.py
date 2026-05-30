from __future__ import annotations

import pytest

from phase3.themes import is_valid_theme
from phase3.validation import ValidationError, validate_deep_result, validate_relevance_result


def test_theme_slugs():
    assert is_valid_theme("user_trust_breakdown")
    assert not is_valid_theme("match_trust_loss")


def test_validate_relevance_result():
    texts = {"p1": "User lost trust after a wrong answer."}
    row = validate_relevance_result(
        {
            "id": "p1",
            "relevant": True,
            "relevance_score": 0.9,
            "reason": "Discusses trust erosion after incorrect output.",
        },
        post_texts=texts,
    )
    assert row["relevant"] is True


def test_validate_deep_result_quote_must_be_substring():
    text = "ChatGPT gave me a hallucination and I lost trust."
    # The self-healing validator should fall back to a substring of the text if the quote is not found,
    # rather than raising a ValidationError.
    row_healed = validate_deep_result(
        {
            "id": "p1",
            "primary_theme": "overconfident_incorrect_outputs",
            "secondary_themes": [],
            "theme_rationale": "Fabricated content.",
            "evidence_quote": "not in post",
            "severity": "medium",
            "model_confidence": 0.8,
        },
        post_texts={"p1": text},
    )
    assert row_healed["evidence_quote"] == text[:100].strip()

    row = validate_deep_result(
        {
            "id": "p1",
            "primary_theme": "overconfident_incorrect_outputs",
            "secondary_themes": ["user_trust_breakdown"],
            "theme_rationale": "Hallucination undermined trust.",
            "evidence_quote": "hallucination",
            "severity": "high",
            "model_confidence": 0.85,
        },
        post_texts={"p1": text},
    )
    assert row["primary_theme"] == "overconfident_incorrect_outputs"
