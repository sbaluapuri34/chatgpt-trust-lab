"""Run Phase 1 collection: python -m phase1 (blocked when PHASE_1_LOCKED)."""

from __future__ import annotations

import argparse
import sys

from phase1.collector import collect_posts
from project.checkpoint import Phase1LockedError, assert_collection_allowed


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 collection")
    parser.add_argument(
        "--allow-new-collection",
        action="store_true",
        help="Explicitly allow a new collection run",
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
