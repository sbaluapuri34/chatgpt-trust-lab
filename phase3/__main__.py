"""Run Phase 3: python -m phase3 [--mock]"""

from __future__ import annotations

import argparse
import logging
import sys

from phase3.deep_analysis import run_deep_analysis
from phase3.plan_batches import plan_deep_batches, plan_relevance_batches
from phase3.relevance import run_relevance

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3: LLM relevance + research theme analysis")
    parser.add_argument("--db", type=str, help="SQLite database path")
    parser.add_argument("--force", action="store_true", help="Re-run batches even if cache exists")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock LLM (no API keys). Auto-enabled when keys are missing.",
    )
    parser.add_argument(
        "--step",
        choices=("all", "plan-relevance", "plan-deep", "relevance", "deep"),
        default="all",
    )
    args = parser.parse_args(argv)
    db_path = args.db
    use_mock = args.mock

    if args.step in ("all", "plan-relevance"):
        path = plan_relevance_batches(db_path=db_path)
        logger.info("Relevance batch plan: %s", path)

    if args.step in ("all", "relevance"):
        summary = run_relevance(db_path=db_path, force=args.force, use_mock=use_mock)
        logger.info("Relevance: %s", summary)

    if args.step in ("all", "plan-deep"):
        path = plan_deep_batches(db_path=db_path)
        logger.info("Deep batch plan: %s", path)

    if args.step in ("all", "deep"):
        summary = run_deep_analysis(db_path=db_path, force=args.force, use_mock=use_mock)
        logger.info("Deep analysis: %s", summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
