"""Phase 3 Stage 1: relevance filter."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase3.relevance import run_relevance  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 3 Stage 1 relevance filter")
    parser.add_argument("--db", type=str)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    summary = run_relevance(db_path=args.db, force=args.force, use_mock=args.mock)
    logging.info("Done: %s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
