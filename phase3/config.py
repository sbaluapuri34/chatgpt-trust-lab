from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ResearchTheme:
    slug: str
    label: str


@dataclass(frozen=True)
class BatchingConfig:
    target_posts_min: int
    target_posts_max: int
    max_input_tokens: int
    max_text_chars: int
    reserved_system_tokens: int
    reserved_output_tokens_relevance: int
    reserved_output_tokens_deep: int
    include_keyword_summary: bool


@dataclass(frozen=True)
class GroqConfig:
    model: str
    base_url: str


@dataclass(frozen=True)
class GeminiConfig:
    model: str


@dataclass(frozen=True)
class LLMConfig:
    primary: str
    fallback: str
    groq: GroqConfig
    gemini: GeminiConfig
    batching: BatchingConfig
    relevance_threshold: float


@dataclass(frozen=True)
class Phase3Config:
    research_themes: tuple[ResearchTheme, ...]
    db_path: Path
    batches_dir: Path
    relevance_prompt_path: Path
    deep_prompt_path: Path
    llm: LLMConfig
    groq_api_key: str | None
    gemini_api_key: str | None


def load_phase3_config(path: Path | str | None = None) -> Phase3Config:
    root = Path(__file__).resolve().parent.parent
    config_path = Path(path) if path else root / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    output = raw["output"]
    llm_raw = raw.get("llm", {})
    batching_raw = llm_raw.get("batching", {})
    groq_raw = llm_raw.get("groq", llm_raw.get("grok", {}))
    gemini_raw = llm_raw.get("gemini", {})

    themes: list[ResearchTheme] = []
    for entry in raw.get("research_themes", []):
        themes.append(ResearchTheme(slug=str(entry["slug"]), label=str(entry["label"])))

    batching = BatchingConfig(
        target_posts_min=int(batching_raw.get("target_posts_min", 50)),
        target_posts_max=int(batching_raw.get("target_posts_max", 100)),
        max_input_tokens=int(batching_raw.get("max_input_tokens", 120_000)),
        max_text_chars=int(batching_raw.get("max_text_chars", 6000)),
        reserved_system_tokens=int(batching_raw.get("reserved_system_tokens", 2000)),
        reserved_output_tokens_relevance=int(batching_raw.get("reserved_output_tokens_relevance", 4000)),
        reserved_output_tokens_deep=int(batching_raw.get("reserved_output_tokens_deep", 8000)),
        include_keyword_summary=bool(batching_raw.get("include_keyword_summary", True)),
    )

    primary_name = str(llm_raw.get("primary", "groq"))
    if primary_name == "grok":
        primary_name = "groq"

    llm = LLMConfig(
        primary=primary_name,
        fallback=str(llm_raw.get("fallback", "gemini")),
        groq=GroqConfig(
            model=str(groq_raw.get("model", "llama-3.3-70b-versatile")),
            base_url=str(groq_raw.get("base_url", "https://api.groq.com/openai/v1")).rstrip("/"),
        ),
        gemini=GeminiConfig(model=str(gemini_raw.get("model", "gemini-2.0-flash"))),
        batching=batching,
        relevance_threshold=float(llm_raw.get("relevance_threshold", 0.5)),
    )

    prompts_dir = root / "prompts"
    return Phase3Config(
        research_themes=tuple(themes),
        db_path=Path(output["db_path"]),
        batches_dir=Path(output.get("batches_dir", "data/batches")),
        relevance_prompt_path=prompts_dir / "relevance_v1.txt",
        deep_prompt_path=prompts_dir / "deep_analysis_v1.txt",
        llm=llm,
        groq_api_key=os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY") or None,
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
    )
