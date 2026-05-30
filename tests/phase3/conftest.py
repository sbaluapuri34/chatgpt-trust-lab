from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from phase2.config import load_phase2_config
from phase2.ingest import ingest_raw_posts
from phase2.preprocess import preprocess_posts
from phase2.select_candidates import select_candidates
from phase3.config import Phase3Config, load_phase3_config

FIXTURES_DIR = Path(__file__).parent.parent / "phase2" / "fixtures"
SAMPLE_POSTS = FIXTURES_DIR / "sample_posts.json"


@pytest.fixture
def sample_raw_path() -> Path:
    return SAMPLE_POSTS


@pytest.fixture
def seeded_db(tmp_path: Path, sample_raw_path: Path) -> Path:
    """Phase 2 complete on fixture posts (2 candidates: post_high, post_mid)."""
    db_path = tmp_path / "research.db"
    phase2_cfg = replace(
        load_phase2_config(),
        db_path=db_path,
        aggregated_dir=tmp_path / "aggregated",
        raw_dir=FIXTURES_DIR,
    )
    ingest_raw_posts(raw_path=sample_raw_path, db_path=db_path, config=phase2_cfg)
    preprocess_posts(db_path=db_path, config=phase2_cfg)
    select_candidates(db_path=db_path, config=phase2_cfg)
    return db_path


@pytest.fixture
def phase3_config(tmp_path: Path, seeded_db: Path) -> Phase3Config:
    base = load_phase3_config()
    return replace(
        base,
        db_path=seeded_db,
        batches_dir=tmp_path / "batches",
    )


@pytest.fixture
def has_groq_key(phase3_config: Phase3Config) -> bool:
    return bool(phase3_config.groq_api_key)


@pytest.fixture
def has_gemini_key(phase3_config: Phase3Config) -> bool:
    return bool(phase3_config.gemini_api_key)
