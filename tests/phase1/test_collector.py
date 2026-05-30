from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from phase1.collector import (
    PostCollector,
    build_manifest,
    collect_posts,
    dedupe_posts,
    post_passes_collection_filters,
    save_collection,
    scraped_to_post,
)
from phase1.config import ListingConfig, load_config
from phase1.parser import ScrapedPost
from phase1.playwright_scraper import MockListingScraper
from tests.phase1.conftest import FIXTURES_DIR

SEARCH_QUERY_COUNT = 16


def test_load_config_scraper():
    config = load_config()
    assert config.scraper.engine == "playwright"
    assert config.scraper.base_url == "https://old.reddit.com"
    assert list(config.subreddits) == ["ChatGPT"]
    assert len(config.search_queries) == SEARCH_QUERY_COUNT
    search_listings = [listing for listing in config.listings if listing.type == "search"]
    assert len(search_listings) == SEARCH_QUERY_COUNT
    assert search_listings[0].query == "confidently wrong"
    assert config.scraper.max_pages_per_search > 0
    assert config.fetch_full_post_content is True


def test_post_passes_collection_filters_no_keyword(now_utc: datetime):
    post = scraped_to_post(
        ScrapedPost(
            id="x1",
            subreddit="ChatGPT",
            title="General",
            selftext="Any topic",
            score=1,
            created_utc=now_utc.timestamp(),
            url="https://old.reddit.com/x",
        )
    )
    floor = now_utc - timedelta(days=270)
    assert post_passes_collection_filters(
        post, date_floor=floor, min_text_chars=1, allowed_subreddits={"ChatGPT"}
    )


def test_build_manifest_includes_search_metadata(now_utc: datetime):
    config = load_config()
    post = scraped_to_post(
        ScrapedPost("id1", "ChatGPT", "t", "b", 1, now_utc.timestamp(), "https://r/1")
    )
    manifest = build_manifest(
        [post],
        config,
        date_floor=now_utc - timedelta(days=270),
        collected_at=now_utc,
        run_id="run",
        listings_executed=[],
        stopped_reasons={},
    )
    assert manifest["collection_strategy"] == "listings_plus_keyword_search"
    assert manifest["search_query_count"] == SEARCH_QUERY_COUNT


def test_enrich_full_post_content(now_utc: datetime, config):
    page_new = (FIXTURES_DIR / "listing_new.html").read_text(encoding="utf-8")
    detail = (FIXTURES_DIR / "post_detail_abc111.html").read_text(encoding="utf-8")
    minimal = replace(
        config,
        search_queries=(),
        fetch_full_post_content=True,
        listings=(ListingConfig(type="new"),),
    )
    mock = MockListingScraper(
        {("ChatGPT", "new"): [page_new]},
        post_details={"abc111": detail},
    )
    posts, manifest = PostCollector(minimal, mock).collect()
    post = next(p for p in posts if p.id == "abc111")
    assert "confidently wrong" in post.selftext
    assert "Real consequence" in post.selftext
    assert manifest["fetch_full_post_content"] is True
    assert manifest["full_content_stats"]["enriched"] >= 1


def test_collector_dedupes_search_with_listings(now_utc: datetime, config):
    page_new = (FIXTURES_DIR / "listing_new.html").read_text(encoding="utf-8")
    page_search = (FIXTURES_DIR / "listing_search_hallucination.html").read_text(encoding="utf-8")
    minimal = replace(
        config,
        search_queries=("hallucination",),
        listings=(
            ListingConfig(type="new"),
            ListingConfig(
                type="search",
                query="hallucination",
                time_filter="year",
                sort="relevance",
            ),
        ),
    )
    mock = MockListingScraper(
        {
            ("ChatGPT", "new"): [page_new],
            ("ChatGPT", "search", "hallucination"): [page_search],
        }
    )
    posts, manifest = PostCollector(minimal, mock).collect()
    by_id = {p.id: p for p in posts}
    assert by_id["abc111"].score == 200
    assert "search_only" in by_id
    assert manifest["search_query_count"] == 1


def test_collector_with_mock_scraper(now_utc: datetime, config):
    page1 = (FIXTURES_DIR / "listing_new.html").read_text(encoding="utf-8")
    page2 = (FIXTURES_DIR / "listing_new_page2.html").read_text(encoding="utf-8")
    minimal = replace(
        config,
        search_queries=(),
        listings=(
            ListingConfig(type="new"),
            ListingConfig(type="top", time_filter="year"),
        ),
    )
    mock = MockListingScraper({("ChatGPT", "new"): [page1, page2], ("ChatGPT", "top"): []})

    posts, manifest = PostCollector(minimal, mock).collect()

    ids = {p.id for p in posts}
    assert "abc111" in ids
    assert "abc333" in ids
    assert "abc999" not in ids
    assert manifest["keyword_filter_at_collection"] is False


def test_collect_posts_injected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config):
    page1 = (FIXTURES_DIR / "listing_new.html").read_text(encoding="utf-8")
    mock = MockListingScraper({("ChatGPT", "new"): [page1], ("ChatGPT", "top"): []})
    tmp_config = replace(
        config,
        raw_dir=tmp_path,
        search_queries=(),
        fetch_full_post_content=False,  # unit test only — production config keeps true
        listings=(ListingConfig(type="new"),),
    )

    monkeypatch.setattr("phase1.collector.load_config", lambda path=None: tmp_config)

    posts, manifest, paths = collect_posts(listing_scraper=mock)
    assert len(posts) >= 2
    assert paths[0].exists()


def test_dedupe_keeps_higher_score():
    from phase1.collector import RedditPost

    posts = [
        RedditPost("x1", "ChatGPT", "t", "b", 10, 1.0, "u"),
        RedditPost("x1", "ChatGPT", "t", "b", 99, 1.0, "u"),
    ]
    assert dedupe_posts(posts)[0].score == 99


def test_save_collection_schema(tmp_path: Path, now_utc: datetime):
    config = load_config()
    post = scraped_to_post(
        ScrapedPost("id1", "ChatGPT", "title", "body", 5, now_utc.timestamp(), "https://r/x")
    )
    manifest = build_manifest(
        [post],
        config,
        date_floor=now_utc - timedelta(days=1),
        collected_at=now_utc,
        run_id="s",
        listings_executed=[],
        stopped_reasons={},
    )
    path, _ = save_collection([post], manifest, tmp_path, collected_at=now_utc)
    row = json.loads(path.read_text(encoding="utf-8"))[0]
    assert set(row.keys()) == {"id", "subreddit", "title", "selftext", "score", "created_utc", "url"}


@pytest.mark.integration
def test_live_playwright_scrape():
    try:
        from playwright.sync_api import sync_playwright

        sync_playwright().start().chromium.launch().close()
    except Exception:
        pytest.skip("Playwright browsers not installed")

    posts, manifest, _ = collect_posts()
    assert manifest["subreddits"] == ["ChatGPT"]
    assert manifest["search_query_count"] == SEARCH_QUERY_COUNT
    assert isinstance(posts, list)
