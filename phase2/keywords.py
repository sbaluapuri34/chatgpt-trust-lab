from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordMatchResult:
    keyword_match_count: int
    match_confidence: int
    match_hallucinations: int
    match_trust: int
    match_trust_loss: int
    match_consequences: int
    category_hit_count: int


# Maps config category keys to KeywordMatchResult field names.
CATEGORY_FIELDS = {
    "confidence": "match_confidence",
    "hallucinations": "match_hallucinations",
    "trust": "match_trust",
    "trust_loss": "match_trust_loss",
    "consequences": "match_consequences",
}


def count_phrase_occurrences(text: str, phrase: str) -> int:
    """Case-insensitive substring count (each non-overlapping match counts once)."""
    phrase = phrase.strip()
    if not phrase:
        return 0
    return len(re.findall(re.escape(phrase), text, flags=re.IGNORECASE))


def count_category_hits(text: str, keywords: tuple[str, ...]) -> int:
    return sum(count_phrase_occurrences(text, keyword) for keyword in keywords)


def analyze_text(
    text: str,
    keyword_categories: dict[str, tuple[str, ...]],
) -> KeywordMatchResult:
    """
    Count keyword hits per category on combined post text.

    keyword_match_count sums occurrence counts across all keywords and categories.
  Each phrase match increments the total; category_hit_count is the number of
    categories with at least one hit (0–5).
    """
    per_category: dict[str, int] = {}
    for category, keywords in keyword_categories.items():
        per_category[category] = count_category_hits(text, keywords)

    keyword_match_count = sum(per_category.values())
    category_hit_count = sum(1 for count in per_category.values() if count > 0)

    return KeywordMatchResult(
        keyword_match_count=keyword_match_count,
        match_confidence=per_category.get("confidence", 0),
        match_hallucinations=per_category.get("hallucinations", 0),
        match_trust=per_category.get("trust", 0),
        match_trust_loss=per_category.get("trust_loss", 0),
        match_consequences=per_category.get("consequences", 0),
        category_hit_count=category_hit_count,
    )
