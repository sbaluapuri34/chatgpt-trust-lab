import json
from pathlib import Path

quotes_path = Path("data/aggregated/representative_quotes.json")
with quotes_path.open(encoding="utf-8") as f:
    quotes = json.load(f)

themes = [
    "persuasive_outputs_trust_formation",
    "user_evaluation_verification_behavior",
    "real_world_impact_of_ai_outputs"
]

for theme in themes:
    print(f"\nTHEME: {theme}")
    theme_quotes = quotes.get(theme, [])
    for idx, q in enumerate(theme_quotes):
        print(f"Rank {idx+1}: Url: {q['url']}")
        print(f"  Quote: {q['evidence_quote']}")
        print(f"  Rationale: {q['theme_rationale']}")
