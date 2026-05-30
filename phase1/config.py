from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ListingConfig:
    type: str  # "new" | "top" | "search"
    time_filter: str | None = None
    query: str | None = None
    sort: str | None = None


@dataclass(frozen=True)
class ScraperConfig:
    engine: str
    base_url: str
    browser: str
    headless: bool
    page_delay_seconds: float
    navigation_timeout_ms: int
    max_pages_per_listing: int
    max_pages_per_search: int


@dataclass(frozen=True)
class CollectionConfig:
    months_back: int
    min_text_chars: int
    fetch_full_post_content: bool
    subreddits: tuple[str, ...]
    listings: tuple[ListingConfig, ...]
    search_queries: tuple[str, ...]
    scraper: ScraperConfig
    raw_dir: Path
    max_posts: int | None = None


def load_config(path: Path | str | None = None) -> CollectionConfig:
    config_path = Path(path) if path else Path(__file__).resolve().parent.parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    collection = raw["collection"]
    output = raw["output"]
    scraper_raw = raw["scraper"]

    listings: list[ListingConfig] = []
    for entry in collection["listings"]:
        listings.append(
            ListingConfig(
                type=str(entry["type"]),
                time_filter=str(entry["time_filter"]) if entry.get("time_filter") else None,
                query=str(entry["query"]) if entry.get("query") else None,
                sort=str(entry["sort"]) if entry.get("sort") else None,
            )
        )

    search_time = str(collection.get("search_time_filter", "year"))
    search_sort = str(collection.get("search_sort", "relevance"))
    for query in collection.get("search_queries", []):
        listings.append(
            ListingConfig(
                type="search",
                query=str(query).strip(),
                time_filter=search_time,
                sort=search_sort,
            )
        )

    max_posts_raw = collection.get("max_posts")
    max_posts = int(max_posts_raw) if max_posts_raw is not None else None

    scraper = ScraperConfig(
        engine=str(scraper_raw.get("engine", "playwright")),
        base_url=str(scraper_raw.get("base_url", "https://old.reddit.com")).rstrip("/"),
        browser=str(scraper_raw.get("browser", "chromium")),
        headless=bool(scraper_raw.get("headless", True)),
        page_delay_seconds=float(scraper_raw.get("page_delay_seconds", 2.0)),
        navigation_timeout_ms=int(scraper_raw.get("navigation_timeout_ms", 45000)),
        max_pages_per_listing=int(scraper_raw.get("max_pages_per_listing", 500)),
        max_pages_per_search=int(scraper_raw.get("max_pages_per_search", 30)),
    )

    search_queries = tuple(str(q).strip() for q in collection.get("search_queries", []))

    return CollectionConfig(
        months_back=int(collection["months_back"]),
        min_text_chars=int(collection["min_text_chars"]),
        # Default true: full post bodies required for research evidence quality
        fetch_full_post_content=bool(collection.get("fetch_full_post_content", True)),
        subreddits=tuple(collection["subreddits"]),
        listings=tuple(listings),
        search_queries=search_queries,
        scraper=scraper,
        raw_dir=Path(output["raw_dir"]),
        max_posts=max_posts,
    )


def all_listing_tasks(config: CollectionConfig) -> tuple[ListingConfig, ...]:
    """Every collection task: browse listings + one search task per query."""
    return config.listings
