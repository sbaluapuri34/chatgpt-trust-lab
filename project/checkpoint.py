from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parent.parent
_STATE_PATH = _ROOT / "project_state.yaml"


class Phase1LockedError(RuntimeError):
    """Raised when a new Phase 1 collection is attempted while the dataset is locked."""


def load_project_state(path: Path | str | None = None) -> dict[str, Any]:
    state_path = Path(path) if path else _STATE_PATH
    if not state_path.exists():
        return {"PHASE_1_LOCKED": False}
    with state_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def is_phase1_locked(state: dict[str, Any] | None = None) -> bool:
    data = state if state is not None else load_project_state()
    return bool(data.get("PHASE_1_LOCKED", False))


# Module-level marker requested for downstream imports.
_state = load_project_state()
PHASE_1_LOCKED: bool = is_phase1_locked(_state)


def get_authoritative_posts_path(root: Path | None = None) -> Path:
    root = root or _ROOT
    state = load_project_state()
    rel = state.get("authoritative_dataset", {}).get("posts_file", "data/raw/posts_20260529.json")
    return (root / rel).resolve()


def get_authoritative_manifest_path(root: Path | None = None) -> Path:
    root = root or _ROOT
    state = load_project_state()
    rel = state.get("authoritative_dataset", {}).get("manifest_file", "data/raw/collection_manifest.json")
    return (root / rel).resolve()


def resolve_raw_posts_path(raw_dir: Path, *, explicit_path: Path | str | None = None) -> Path:
    """Return the raw posts JSON path. When Phase 1 is locked, always use the authoritative file."""
    if explicit_path is not None:
        return Path(explicit_path).resolve()
    if is_phase1_locked():
        return get_authoritative_posts_path()
    candidates = sorted(raw_dir.glob("posts_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No posts_*.json files found in {raw_dir}")
    return candidates[0].resolve()


def assert_collection_allowed(*, allow_new_collection: bool = False) -> None:
    """
    Block new Reddit collection when PHASE_1_LOCKED is true.

    Pass allow_new_collection=True only via an explicit CLI flag after owner confirmation.
    """
    if is_phase1_locked() and not allow_new_collection:
        posts = get_authoritative_posts_path()
        raise Phase1LockedError(
            "PHASE_1_LOCKED=TRUE: Phase 1 collection is complete and immutable. "
            f"Authoritative dataset: {posts}. "
            "Do not recollect unless you explicitly request a new run with "
            "`python scripts/collect.py --allow-new-collection` after confirming with the project owner."
        )
