from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tiktoken

from phase3.config import BatchingConfig


@dataclass(frozen=True)
class BatchPlan:
    stage: str
    batches: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "batch_count": len(self.batches),
            "batches": [list(batch) for batch in self.batches],
        }


def get_encoding():
    try:
        return tiktoken.encoding_for_model("gpt-4o")
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(get_encoding().encode(text))


def estimate_post_tokens(post: dict[str, Any]) -> int:
    return count_tokens(json.dumps(post, ensure_ascii=False))


def post_token_budget(batching: BatchingConfig, *, reserved_output_tokens: int) -> int:
    return (
        batching.max_input_tokens
        - batching.reserved_system_tokens
        - reserved_output_tokens
    )


def plan_batches(
    posts: list[dict[str, Any]],
    *,
    stage: str,
    batching: BatchingConfig,
    reserved_output_tokens: int,
) -> BatchPlan:
    if not posts:
        return BatchPlan(stage=stage, batches=())

    budget = post_token_budget(batching, reserved_output_tokens=reserved_output_tokens)
    batches: list[list[str]] = []
    current_ids: list[str] = []
    current_tokens = 0

    for post in posts:
        post_id = str(post["id"])
        tokens = estimate_post_tokens(post)
        if tokens > budget and not current_ids:
            batches.append([post_id])
            continue

        if current_ids and (current_tokens + tokens > budget or len(current_ids) >= batching.target_posts_max):
            batches.append(current_ids)
            current_ids = []
            current_tokens = 0

        current_ids.append(post_id)
        current_tokens += tokens

        if len(current_ids) >= batching.target_posts_max:
            batches.append(current_ids)
            current_ids = []
            current_tokens = 0

    if current_ids:
        batches.append(current_ids)

    merged: list[list[str]] = []
    for batch in batches:
        if merged and len(batch) < batching.target_posts_min and len(merged[-1]) + len(batch) <= batching.target_posts_max:
            merged[-1].extend(batch)
        else:
            merged.append(batch)

    return BatchPlan(stage=stage, batches=tuple(tuple(batch) for batch in merged))


def save_batch_plan(plan: BatchPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, indent=2)


def load_batch_plan(path: Path) -> BatchPlan:
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    batches = tuple(tuple(batch) for batch in raw["batches"])
    return BatchPlan(stage=str(raw["stage"]), batches=batches)
