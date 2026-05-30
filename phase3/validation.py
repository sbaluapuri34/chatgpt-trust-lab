from __future__ import annotations

import json
from typing import Any

from phase3.themes import SEVERITY_VALUES, is_valid_theme


class ValidationError(ValueError):
    pass


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    raise ValidationError(f"Invalid boolean: {value!r}")


def _clamp_score(value: Any, field: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a number") from exc
    if not 0.0 <= score <= 1.0:
        raise ValidationError(f"{field} must be between 0 and 1")
    return score


def validate_relevance_result(item: dict[str, Any], *, post_texts: dict[str, str]) -> dict[str, Any]:
    post_id = str(item.get("id", "")).strip()
    if not post_id:
        raise ValidationError("Missing post id in relevance result")
    if post_id not in post_texts:
        raise ValidationError(f"Unknown post id in relevance result: {post_id}")

    relevant = _normalize_bool(item["relevant"])
    relevance_score = _clamp_score(item.get("relevance_score", 0.0), "relevance_score")
    reason = str(item.get("reason", "")).strip()
    if not reason:
        reason = "Relevance assessed by Groq model."

    return {
        "id": post_id,
        "relevant": relevant,
        "relevance_score": relevance_score,
        "reason": reason,
    }


def validate_deep_result(item: dict[str, Any], *, post_texts: dict[str, str]) -> dict[str, Any]:
    post_id = str(item.get("id", "")).strip()
    if not post_id:
        raise ValidationError("Missing post id in deep analysis result")
    if post_id not in post_texts:
        raise ValidationError(f"Unknown post id in deep analysis result: {post_id}")

    text = post_texts[post_id]
    primary_theme = str(item.get("primary_theme", "")).strip()
    if not is_valid_theme(primary_theme):
        primary_theme = "mixed_or_multitheme"

    raw_secondary = item.get("secondary_themes") or []
    if not isinstance(raw_secondary, list):
        raw_secondary = []
    secondary_themes: list[str] = []
    for theme in raw_secondary[:3]:
        slug = str(theme).strip()
        if slug == primary_theme:
            continue
        if not is_valid_theme(slug):
            continue
        if slug not in secondary_themes:
            secondary_themes.append(slug)

    theme_rationale = str(item.get("theme_rationale", "")).strip()
    if not theme_rationale:
        theme_rationale = "Theme assigned by Groq model."

    evidence_quote = str(item.get("evidence_quote", "")).strip()
    if not evidence_quote or evidence_quote not in text:
        evidence_quote = text[:100].strip() if text else "N/A"

    severity = str(item.get("severity", "")).strip().lower()
    if severity not in SEVERITY_VALUES:
        severity = "medium"

    model_confidence = _clamp_score(item.get("model_confidence", 0.0), "model_confidence")

    raw_labels = item.get("secondary_labels") or []
    secondary_labels: list[str] = []
    if isinstance(raw_labels, list):
        secondary_labels = [str(label).strip() for label in raw_labels if str(label).strip()]

    return {
        "id": post_id,
        "primary_theme": primary_theme,
        "secondary_themes": secondary_themes,
        "theme_rationale": theme_rationale,
        "evidence_quote": evidence_quote,
        "severity": severity,
        "model_confidence": model_confidence,
        "secondary_labels": secondary_labels,
    }


def validate_relevance_batch(
    results: list[dict[str, Any]],
    *,
    expected_ids: set[str],
    post_texts: dict[str, str],
) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in results:
        try:
            row = validate_relevance_result(item, post_texts=post_texts)
            seen.add(row["id"])
            validated.append(row)
        except Exception:
            pass
    missing = expected_ids - seen
    for pid in missing:
        validated.append({
            "id": pid,
            "relevant": False,
            "relevance_score": 0.0,
            "reason": "Fallback: Post omitted or malformed in LLM response."
        })
    return validated


def validate_deep_batch(
    results: list[dict[str, Any]],
    *,
    expected_ids: set[str],
    post_texts: dict[str, str],
) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in results:
        try:
            row = validate_deep_result(item, post_texts=post_texts)
            seen.add(row["id"])
            validated.append(row)
        except Exception:
            pass
    missing = expected_ids - seen
    for pid in missing:
        validated.append({
            "id": pid,
            "primary_theme": "mixed_or_multitheme",
            "secondary_themes": [],
            "theme_rationale": "Fallback: Post omitted or malformed in LLM response.",
            "evidence_quote": "N/A",
            "severity": "medium",
            "model_confidence": 0.0,
            "secondary_labels": []
        })
    return validated


def themes_to_json(themes: list[str]) -> str:
    return json.dumps(themes, ensure_ascii=False)


def labels_to_json(labels: list[str]) -> str:
    return json.dumps(labels, ensure_ascii=False)
