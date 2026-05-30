import os
import json
import sqlite3
from pathlib import Path
from phase3.config import load_phase3_config
from phase3.db import get_db_connection
from phase3.payloads import load_candidate_posts
from phase3.batching import plan_batches, BatchPlan, save_batch_plan

def main():
    cfg = load_phase3_config()
    database = cfg.db_path
    conn = get_db_connection(database)
    all_posts = load_candidate_posts(conn, include_keyword_summary=cfg.llm.batching.include_keyword_summary)
    conn.close()

    print(f"Total candidate posts in database: {len(all_posts)}")

    # Load all available cached batches dynamically
    cached_batches = []
    covered_ids = set()

    i = 1
    while True:
        cache_path = cfg.batches_dir / "relevance" / f"batch_{i:03d}_results.json"
        if not cache_path.exists():
            break
        with cache_path.open(encoding="utf-8") as f:
            data = json.load(f)
        ids = [str(x) for x in data["post_ids"]]
        cached_batches.append(tuple(ids))
        covered_ids.update(ids)
        i += 1

    num_cached = i - 1
    print(f"Loaded {num_cached} cached batches from disk.")
    print(f"Covered posts in batches 1-{num_cached}: {len(covered_ids)}")

    # Find remaining posts
    remaining_posts = [p for p in all_posts if str(p["id"]) not in covered_ids]
    print(f"Remaining posts to plan: {len(remaining_posts)}")

    # Plan remaining batches
    remaining_plan = plan_batches(
        remaining_posts,
        stage="relevance",
        batching=cfg.llm.batching,
        reserved_output_tokens=cfg.llm.batching.reserved_output_tokens_relevance,
    )

    print(f"Remaining batches planned: {len(remaining_plan.batches)}")

    # Combine batches
    combined_batches = cached_batches + [tuple(b) for b in remaining_plan.batches]
    combined_plan = BatchPlan(stage="relevance", batches=tuple(combined_batches))

    # Save the combined plan
    plan_path = cfg.batches_dir / "relevance" / "batch_plan.json"
    save_batch_plan(combined_plan, plan_path)
    print(f"Saved combined batch plan to {plan_path} with {len(combined_plan.batches)} total batches.")

if __name__ == "__main__":
    main()
