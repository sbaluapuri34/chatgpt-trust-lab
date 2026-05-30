"""Plan Phase 3 token batches without calling the LLM."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase3.plan_batches import plan_deep_batches, plan_relevance_batches  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Phase 3 LLM batches")
    parser.add_argument("--db", type=str, help="SQLite database path")
    parser.add_argument("--stage", choices=("relevance", "deep", "both"), default="both")
    args = parser.parse_args()

    if args.stage in ("relevance", "both"):
        plan_relevance_batches(db_path=args.db)
    if args.stage in ("deep", "both"):
        plan_deep_batches(db_path=args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
