from __future__ import annotations

from phase3.batching import plan_batches
from phase3.config import BatchingConfig


def _batching() -> BatchingConfig:
    return BatchingConfig(
        target_posts_min=2,
        target_posts_max=3,
        max_input_tokens=500,
        max_text_chars=6000,
        reserved_system_tokens=50,
        reserved_output_tokens_relevance=50,
        reserved_output_tokens_deep=100,
        include_keyword_summary=True,
    )


def test_plan_batches_splits_large_set():
    posts = [{"id": f"p{i}", "text": f"word {i} " * 20, "score": i} for i in range(6)]
    plan = plan_batches(
        posts,
        stage="relevance",
        batching=_batching(),
        reserved_output_tokens=50,
    )
    assert len(plan.batches) >= 2
    all_ids = [post_id for batch in plan.batches for post_id in batch]
    assert sorted(all_ids) == sorted(post["id"] for post in posts)
