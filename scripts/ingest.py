"""Phase 2a entry point: ingest raw JSON into SQLite."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.ingest import ingest_raw_posts  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest raw Reddit JSON into research.db")
    parser.add_argument("--raw", type=str, help="Path to posts_*.json")
    parser.add_argument("--db", type=str, help="SQLite output path")
    args = parser.parse_args()

    summary = ingest_raw_posts(raw_path=args.raw, db_path=args.db)
    logging.info("Done: %s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
