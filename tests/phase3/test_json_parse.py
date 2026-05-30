from __future__ import annotations

from phase3.json_parse import extract_json_array


def test_extract_json_array_from_markdown_fence():
    raw = 'Here is the output:\n```json\n[{"id": "a", "relevant": true}]\n```'
    result = extract_json_array(raw)
    assert result[0]["id"] == "a"
