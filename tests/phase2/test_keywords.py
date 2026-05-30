from __future__ import annotations

from phase2.keywords import analyze_text, count_phrase_occurrences
from phase2.config import load_phase2_config


def test_count_phrase_occurrences_case_insensitive():
    text = "Trust TRUST and trusted replies"
    # Substring matching: "trust" also matches inside "trusted".
    assert count_phrase_occurrences(text, "trust") == 3
    assert count_phrase_occurrences(text, "trusted") == 1


def test_analyze_text_high_relevance_post():
    config = load_phase2_config()
    text = (
        "I was overconfident and lost trust in ChatGPT. "
        "It gave me a hallucination about my health and I made a costly mistake at work."
    )
    result = analyze_text(text, config.keyword_categories)

    assert result.keyword_match_count >= 6
    assert result.match_confidence >= 1
    assert result.match_hallucinations >= 1
    assert result.match_trust >= 1
    assert result.match_trust_loss >= 1
    assert result.match_consequences >= 2
    assert result.category_hit_count == 5


def test_analyze_text_no_keyword_hits():
    config = load_phase2_config()
    result = analyze_text("Funny image generation only", config.keyword_categories)

    assert result.keyword_match_count == 0
    assert result.category_hit_count == 0
