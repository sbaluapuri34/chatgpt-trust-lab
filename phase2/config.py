from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SelectionConfig:
    max_candidates: int
    w_keyword: float
    w_score: float
    category_weight: float
    require_min_keyword_matches: int


@dataclass(frozen=True)
class Phase2Config:
    keyword_categories: dict[str, tuple[str, ...]]
    raw_dir: Path
    db_path: Path
    aggregated_dir: Path
    selection: SelectionConfig


def load_phase2_config(path: Path | str | None = None) -> Phase2Config:
    config_path = Path(path) if path else Path(__file__).resolve().parent.parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    preprocessing = raw["preprocessing"]
    output = raw["output"]
    selection_raw = raw.get("selection", {})

    categories: dict[str, tuple[str, ...]] = {}
    for name, keywords in preprocessing["keyword_categories"].items():
        categories[name] = tuple(str(k).strip() for k in keywords)

    selection = SelectionConfig(
        max_candidates=int(selection_raw.get("max_candidates", 1200)),
        w_keyword=float(selection_raw.get("w_keyword", 0.6)),
        w_score=float(selection_raw.get("w_score", 0.4)),
        category_weight=float(selection_raw.get("category_weight", 2.0)),
        require_min_keyword_matches=int(selection_raw.get("require_min_keyword_matches", 1)),
    )

    return Phase2Config(
        keyword_categories=categories,
        raw_dir=Path(output["raw_dir"]),
        db_path=Path(output.get("db_path", "data/research.db")),
        aggregated_dir=Path(output.get("aggregated_dir", "data/aggregated")),
        selection=selection,
    )
