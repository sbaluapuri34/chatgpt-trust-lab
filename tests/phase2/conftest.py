from __future__ import annotations

from pathlib import Path

import pytest

from phase2.config import Phase2Config, load_phase2_config

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def phase2_config(tmp_path: Path) -> Phase2Config:
    base = load_phase2_config()
    return Phase2Config(
        keyword_categories=base.keyword_categories,
        raw_dir=FIXTURES_DIR,
        db_path=tmp_path / "research.db",
        aggregated_dir=tmp_path / "aggregated",
        selection=base.selection,
    )


@pytest.fixture
def sample_raw_path() -> Path:
    return FIXTURES_DIR / "sample_posts.json"
