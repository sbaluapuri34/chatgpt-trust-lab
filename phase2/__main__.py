"""Run full Phase 2 pipeline: ingest → preprocess → select candidates."""

from __future__ import annotations

import argparse
import logging
import sys

from phase2.ingest import ingest_raw_posts
from phase2.preprocess import preprocess_posts
from phase2.select_candidates import select_candidates

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2: ingest, preprocess, select candidates")
    parser.add_argument("--raw", type=str, help="Path to raw posts JSON (default: latest in data/raw)")
    parser.add_argument("--db", type=str, help="SQLite database path (default: config output.db_path)")
    parser.add_argument(
        "--step",
        choices=("all", "ingest", "preprocess", "select"),
        default="all",
        help="Pipeline step to run",
    )
    args = parser.parse_args(argv)

    if args.step in ("all", "ingest"):
        summary = ingest_raw_posts(raw_path=args.raw, db_path=args.db)
        logger.info("Ingest: %s", summary)

    if args.step in ("all", "preprocess"):
        summary = preprocess_posts(db_path=args.db)
        logger.info("Preprocess: %s", summary)

    if args.step in ("all", "select"):
        report = select_candidates(db_path=args.db)
        logger.info("Selection report: %s", report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
