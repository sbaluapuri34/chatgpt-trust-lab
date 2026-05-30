from __future__ import annotations

import json
import re
from typing import Any


def extract_json_array(text: str) -> list[dict[str, Any]]:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, flags=re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("LLM response did not contain a JSON array") from None
        parsed = json.loads(cleaned[start : end + 1])

    if isinstance(parsed, dict) and "results" in parsed:
        parsed = parsed["results"]
    if not isinstance(parsed, list):
        raise ValueError("LLM response JSON must be an array of post results")
    return [item for item in parsed if isinstance(item, dict)]
