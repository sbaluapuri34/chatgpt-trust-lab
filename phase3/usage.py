from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_usage_log(
    path: Path,
    *,
    stage: str,
    batch_index: int,
    model: str,
    post_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "batch_index": batch_index,
        "model": model,
        "post_count": post_count,
    }
    rows: list[dict[str, Any]] = []
    if path.exists():
        with path.open(encoding="utf-8") as f:
            rows = json.load(f)
    rows.append(entry)
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
