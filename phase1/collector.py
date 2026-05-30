from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from phase1.config import CollectionConfig, ListingConfig, load_config
from phase1.parser import ScrapedPost
from phase1.playwright_scraper import ListingScraper, create_listing_scraper

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedditPost:
    """Collected post — fields aligned with architecture v3.0."""

    id: str
    subreddit: str
    title: str
    selftext: str
    score: int
    created_utc: float
    url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_date_floor(months_back: int, now: datetime | None = None) -> datetime:
    reference = now or datetime.now(timezone.utc)
    return reference - timedelta(days=months_back * 30)


def combined_text(title: str, selftext: str) -> str:
    return f"{title.strip()}\n\n{selftext.strip()}".strip()


def scraped_to_post(scraped: ScrapedPost) -> RedditPost:
    return RedditPost(
        id=scraped.id,
        subreddit=scraped.subreddit,
        title=scraped.title,
        selftext=scraped.selftext,
        score=scraped.score,
        created_utc=scraped.created_utc,
        url=scraped.url,
    )


def post_passes_collection_filters(
    post: RedditPost,
    *,
    date_floor: datetime,
    min_text_chars: int,
    allowed_subreddits: set[str],
) -> bool:
    if post.subreddit.lower() not in {s.lower() for s in allowed_subreddits}:
        return False

    created = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
    if created < date_floor:
        return False

    if len(combined_text(post.title, post.selftext)) < min_text_chars:
        return False

    return True


def dedupe_posts(posts: list[RedditPost]) -> list[RedditPost]:
    by_id: dict[str, RedditPost] = {}
    for post in posts:
        existing = by_id.get(post.id)
        if existing is None or post.score > existing.score:
            by_id[post.id] = post
    return list(by_id.values())


def apply_max_posts(posts: list[RedditPost], max_posts: int | None) -> list[RedditPost]:
    if max_posts is None or len(posts) <= max_posts:
        return posts
    posts_sorted = sorted(posts, key=lambda p: p.created_utc, reverse=True)
    return posts_sorted[:max_posts]


def build_manifest(
    posts: list[RedditPost],
    config: CollectionConfig,
    *,
    date_floor: datetime,
    collected_at: datetime,
    run_id: str,
    listings_executed: list[dict[str, str]],
    stopped_reasons: dict[str, int],
    full_content_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    created_values = [p.created_utc for p in posts]
    config_blob = json.dumps(
        {
            "subreddits": list(config.subreddits),
            "months_back": config.months_back,
            "max_posts": config.max_posts,
            "scraper": {
                "engine": config.scraper.engine,
                "base_url": config.scraper.base_url,
            },
            "keyword_filter_at_collection": False,
            "fetch_full_post_content": config.fetch_full_post_content,
        },
        sort_keys=True,
    )

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "phase": "1",
        "architecture_version": "3.3",
        "collected_at": collected_at.isoformat(),
        "date_floor_utc": date_floor.isoformat(),
        "subreddits": list(config.subreddits),
        "collection_method": "playwright_browser_scrape",
        "collection_strategy": "listings_plus_keyword_search",
        "search_query_count": len(config.search_queries),
        "search_queries": list(config.search_queries),
        "scraper": {
            "engine": config.scraper.engine,
            "base_url": config.scraper.base_url,
            "headless": config.scraper.headless,
        },
        "keyword_filter_at_collection": False,
        "fetch_full_post_content": config.fetch_full_post_content,
        "post_count": len(posts),
        "max_posts_cap": config.max_posts,
        "min_text_chars": config.min_text_chars,
        "date_range": {
            "min_created_utc": min(created_values) if created_values else None,
            "max_created_utc": max(created_values) if created_values else None,
        },
        "listings_executed": listings_executed,
        "stopped_reasons": stopped_reasons,
        "config_hash": hashlib.sha256(config_blob.encode()).hexdigest()[:16],
    }
    if full_content_stats is not None:
        manifest["full_content_stats"] = full_content_stats
    return manifest


class PostCollector:
    """Collect r/ChatGPT posts via Playwright (old.reddit.com listings)."""

    def __init__(self, config: CollectionConfig, listing_scraper: ListingScraper) -> None:
        self._config = config
        self._scraper = listing_scraper

    def collect_from_listing(
        self,
        subreddit_name: str,
        listing: ListingConfig,
        *,
        date_floor: datetime,
        allowed: set[str],
        by_id: dict[str, RedditPost],
    ) -> dict[str, int]:
        stats = {
            "pages": 0,
            "examined": 0,
            "accepted": 0,
            "too_old": 0,
            "updated": 0,
            "filtered": 0,
        }
        date_floor_ts = date_floor.timestamp()
        stop_listing = False

        try:
            for page_posts, _html in self._scraper.iter_listing_pages(subreddit_name, listing):
                stats["pages"] += 1
                if not page_posts and stats["pages"] > 1:
                    break

                page_has_in_window = False
                for scraped in page_posts:
                    stats["examined"] += 1

                    if scraped.created_utc < date_floor_ts:
                        stats["too_old"] += 1
                        # Only /new/ is chronological; stop early. Search/top: skip old, keep paging.
                        if listing.type == "new":
                            stop_listing = True
                        continue

                    page_has_in_window = True
                    post = scraped_to_post(scraped)
                    if not post_passes_collection_filters(
                        post,
                        date_floor=date_floor,
                        min_text_chars=self._config.min_text_chars,
                        allowed_subreddits=allowed,
                    ):
                        stats["filtered"] += 1
                        continue

                    existing = by_id.get(post.id)
                    if existing is None:
                        by_id[post.id] = post
                        stats["accepted"] += 1
                    elif post.score > existing.score:
                        by_id[post.id] = post
                        stats["updated"] += 1

                if stop_listing:
                    break
                if listing.type == "new" and not page_has_in_window and stats["pages"] > 0:
                    break

        except Exception as exc:
            label = listing.query if listing.type == "search" else listing.type
            logger.warning(
                "Scrape failed for r/%s (%s): %s",
                subreddit_name,
                label,
                exc,
            )

        return stats

    def collect(self) -> tuple[list[RedditPost], dict[str, Any]]:
        date_floor = compute_date_floor(self._config.months_back)
        collected_at = datetime.now(timezone.utc)
        run_id = str(uuid.uuid4())
        allowed = set(self._config.subreddits)
        by_id: dict[str, RedditPost] = {}
        listings_executed: list[dict[str, str]] = []
        stopped_reasons: dict[str, int] = {}

        try:
            for subreddit_name in self._config.subreddits:
                for listing in self._config.listings:
                    entry: dict[str, str] = {
                        "subreddit": subreddit_name,
                        "type": listing.type,
                        "time_filter": listing.time_filter or "",
                        "url_base": self._config.scraper.base_url,
                    }
                    if listing.type == "search" and listing.query:
                        entry["query"] = listing.query
                        entry["sort"] = listing.sort or "relevance"
                    listings_executed.append(entry)

                    stats = self.collect_from_listing(
                        subreddit_name,
                        listing,
                        date_floor=date_floor,
                        allowed=allowed,
                        by_id=by_id,
                    )
                    if listing.type == "search" and listing.query:
                        key = f"{subreddit_name}:search:{listing.query}"
                    else:
                        key = f"{subreddit_name}:{listing.type}"
                    stopped_reasons[key] = stats.get("too_old", 0)

            posts = dedupe_posts(list(by_id.values()))
            posts = apply_max_posts(posts, self._config.max_posts)
            posts.sort(key=lambda p: p.created_utc, reverse=True)

            full_content_stats: dict[str, int] = {}
            if self._config.fetch_full_post_content and posts:
                posts, full_content_stats = self._scraper.enrich_full_post_content(posts)

            manifest = build_manifest(
                posts,
                self._config,
                date_floor=date_floor,
                collected_at=collected_at,
                run_id=run_id,
                listings_executed=listings_executed,
                stopped_reasons=stopped_reasons,
                full_content_stats=full_content_stats or None,
            )
            return posts, manifest
        finally:
            self._scraper.close()


def save_collection(
    posts: list[RedditPost],
    manifest: dict[str, Any],
    raw_dir: Path,
    *,
    collected_at: datetime | None = None,
) -> tuple[Path, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = (collected_at or datetime.now(timezone.utc)).strftime("%Y%m%d")
    posts_path = raw_dir / f"posts_{stamp}.json"
    manifest_path = raw_dir / "collection_manifest.json"

    posts_path.write_text(
        json.dumps([p.to_dict() for p in posts], indent=2),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return posts_path, manifest_path


def collect_posts(
    config_path: Path | str | None = None,
    *,
    listing_scraper: ListingScraper | None = None,
) -> tuple[list[RedditPost], dict[str, Any], tuple[Path, Path]]:
    config = load_config(config_path)
    scraper = create_listing_scraper(config, listing_scraper)
    collector = PostCollector(config, scraper)
    posts, manifest = collector.collect()
    paths = save_collection(posts, manifest, config.raw_dir)
    return posts, manifest, paths


__all__ = [
    "PostCollector",
    "RedditPost",
    "collect_posts",
    "load_config",
    "compute_date_floor",
    "combined_text",
    "post_passes_collection_filters",
    "dedupe_posts",
    "apply_max_posts",
    "build_manifest",
    "scraped_to_post",
    "save_collection",
]
