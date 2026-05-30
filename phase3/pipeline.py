from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from phase3.batching import BatchPlan, load_batch_plan, plan_batches, save_batch_plan
from phase3.config import Phase3Config
from phase3.db import get_db_connection
from phase3.json_parse import extract_json_array
from phase3.llm import build_llm_clients, complete_with_fallback
from phase3.payloads import posts_to_text_map, serialize_posts_for_prompt
from phase3.usage import append_usage_log

logger = logging.getLogger(__name__)


def read_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_user_prompt(posts: list[dict[str, Any]]) -> str:
    return (
        "Analyze every post in the JSON array below. Return one result object per post id.\n\n"
        f"POSTS:\n{serialize_posts_for_prompt(posts)}"
    )


def batch_cache_path(batches_dir: Path, stage: str, batch_index: int) -> Path:
    return batches_dir / stage / f"batch_{batch_index:03d}_results.json"


def load_cached_batch(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_cached_batch(
    path: Path,
    *,
    batch_index: int,
    post_ids: list[str],
    model: str,
    results: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "batch_index": batch_index,
        "post_ids": post_ids,
        "model": model,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def run_batches(
    *,
    config: Phase3Config,
    stage: str,
    posts: list[dict[str, Any]],
    plan_path: Path,
    system_prompt_path: Path,
    reserved_output_tokens: int,
    validate_fn: Callable[..., list[dict[str, Any]]],
    persist_fn: Callable[..., None],
    force: bool = False,
    use_mock: bool = False,
    validation_post_texts: dict[str, str] | None = None,
) -> dict[str, int]:
    if not posts:
        logger.info("No posts to process for stage=%s", stage)
        return {"batches_run": 0, "posts_processed": 0}

    post_by_id = {str(post["id"]): post for post in posts}
    post_texts = posts_to_text_map(posts)
    validation_texts = validation_post_texts if validation_post_texts is not None else post_texts

    if plan_path.exists() and not force:
        plan = load_batch_plan(plan_path)
    else:
        plan = plan_batches(
            posts,
            stage=stage,
            batching=config.llm.batching,
            reserved_output_tokens=reserved_output_tokens,
        )
        save_batch_plan(plan, plan_path)

    system_prompt = read_prompt(system_prompt_path)
    clients = build_llm_clients(
        stage=stage,
        primary=config.llm.primary,
        fallback=config.llm.fallback,
        groq_api_key=config.groq_api_key,
        gemini_api_key=config.gemini_api_key,
        groq_config=config.llm.groq,
        gemini_config=config.llm.gemini,
        use_mock=use_mock,
    )

    batches_run = 0
    posts_processed = 0

    for batch_index, post_ids in enumerate(plan.batches, start=1):
        cache_path = batch_cache_path(config.batches_dir, stage, batch_index)
        if cache_path.exists() and not force:
            cached = load_cached_batch(cache_path)
            cached_ids = set(cached.get("post_ids", [])) if cached else set()
            if cached and cached.get("results") and cached_ids == set(post_ids):
                validated = validate_fn(
                    cached["results"],
                    expected_ids=set(post_ids),
                    post_texts=validation_texts,
                )
                persist_fn(validated, model=str(cached.get("model", "cached")))
                posts_processed += len(validated)
                continue

        batch_posts = [post_by_id[post_id] for post_id in post_ids]
        user_prompt = build_user_prompt(batch_posts)
        raw_response, model_name = complete_with_fallback(
            clients,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        parsed = extract_json_array(raw_response)
        validated = validate_fn(parsed, expected_ids=set(post_ids), post_texts=validation_texts)
        save_cached_batch(
            cache_path,
            batch_index=batch_index,
            post_ids=list(post_ids),
            model=model_name,
            results=validated,
        )
        persist_fn(validated, model=model_name)
        append_usage_log(
            config.batches_dir / "llm_usage.json",
            stage=stage,
            batch_index=batch_index,
            model=model_name,
            post_count=len(validated),
        )
        batches_run += 1
        posts_processed += len(validated)
        logger.info("Stage %s batch %s: %s posts via %s", stage, batch_index, len(validated), model_name)
        time.sleep(8)

    return {"batches_run": batches_run, "posts_processed": posts_processed}
