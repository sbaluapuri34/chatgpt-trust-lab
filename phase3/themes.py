from __future__ import annotations

RESEARCH_THEME_SLUGS: frozenset[str] = frozenset(
    {
        "overconfident_incorrect_outputs",
        "user_trust_breakdown",
        "over_reliance_on_ai_outputs",
        "user_evaluation_verification_behavior",
        "real_world_impact_of_ai_outputs",
        "persuasive_outputs_trust_formation",
        "needs_manual_review",
    }
)

SEVERITY_VALUES: frozenset[str] = frozenset({"low", "medium", "high"})


def is_valid_theme(slug: str) -> bool:
    return slug in RESEARCH_THEME_SLUGS


def is_valid_severity(value: str) -> bool:
    return value in SEVERITY_VALUES
