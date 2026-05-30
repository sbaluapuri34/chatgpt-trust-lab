#!/usr/bin/env python3
"""Phase 1 entry point: collect Reddit posts (blocked when PHASE_1_LOCKED)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase1.collector import collect_posts  # noqa: E402
from project.checkpoint import Phase1LockedError, assert_collection_allowed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1: collect r/ChatGPT posts")
    parser.add_argument(
        "--allow-new-collection",
        action="store_true",
        help="Explicitly allow a new collection run (Phase 1 is normally locked)",
    )
    args = parser.parse_args()

    try:
        assert_collection_allowed(allow_new_collection=args.allow_new_collection)
    except Phase1LockedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    posts, manifest, (posts_path, manifest_path) = collect_posts()
    print(f"Collected {len(posts)} posts")
    print(f"Posts file: {posts_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Run ID: {manifest['run_id']}")
    print(
        "NOTE: A new collection file was written. The locked authoritative dataset "
        "is unchanged unless you manually update project_state.yaml."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
