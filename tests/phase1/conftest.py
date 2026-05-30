from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from phase1.config import CollectionConfig, load_config

FIXTURES_DIR = Path(__file__).parent / "fixtures"







@pytest.fixture
def now_utc() -> datetime:
    return datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def config() -> CollectionConfig:
    return load_config()
