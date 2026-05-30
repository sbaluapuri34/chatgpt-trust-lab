from __future__ import annotations

import logging
import time
import json
import random
import urllib.request
import urllib.error
from dataclasses import replace
from typing import Any, Iterator, Protocol

from phase1.config import CollectionConfig, ListingConfig
from phase1.parser import (
    ScrapedPost,
    find_next_page_url,
    merge_selftext,
    parse_listing_page,
    parse_post_detail_page,
    resolve_listing_start_url,
    normalize_scraped_url,
)

logger = logging.getLogger(__name__)


class PersistentSession:
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self.cookie_jar = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(self.cookie_jar)
        self.opener.addheaders = [("User-Agent", self.user_agent)]

    def get_json(self, url: str) -> dict:
        try:
            endpoint = url.replace("old.reddit.com", "www.reddit.com")
            with self.opener.open(endpoint, timeout=15) as response:
                content = response.read().decode("utf-8")
                return json.loads(content)
        except Exception as e:
            logger.warning("Error fetching JSON from %s: %s", url, e)
            raise


def _mock_page_key(subreddit: str, listing: ListingConfig) -> tuple[str, ...]:
    if listing.type == "search":
        return (subreddit, "search", listing.query or "")
    return (subreddit, listing.type)


def max_pages_for_listing(scraper: CollectionConfig, listing: ListingConfig) -> int:
    if listing.type == "search":
        return scraper.scraper.max_pages_per_search
    return scraper.scraper.max_pages_per_listing


class ListingScraper(Protocol):
    def iter_listing_pages(
        self,
        subreddit: str,
        listing: ListingConfig,
    ) -> Iterator[tuple[list[ScrapedPost], str]]: ...

    def enrich_full_post_content(self, posts: list[Any]) -> tuple[list[Any], dict[str, int]]: ...

    def close(self) -> None: ...


class PlaywrightListingScraper:
    """Browser-based scraper for old.reddit.com listings, search, and post pages."""

    def __init__(self, config: CollectionConfig) -> None:
        self._config = config
        self._scraper = config.scraper
        self._session = PersistentSession(
            user_agent="script:reddit-analyser:v3.4 (by /u/academic_researcher)"
        )
        self._json_blocked = False
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _ensure_browser(self) -> None:
        if self._browser is not None:
            return
        from playwright.sync_api import sync_playwright
        logger.info("Initializing persistent Playwright browser session...")
        self._playwright = sync_playwright().start()
        self._browser = self._launch_browser(self._playwright)
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        self._page = self._context.new_page()
        
        # Performance optimization: Block images, stylesheets, fonts, and media
        def block_resources(route):
            r_type = route.request.resource_type
            if r_type in ("image", "stylesheet", "font", "media"):
                route.abort()
            else:
                route.continue_()
        self._page.route("**/*", block_resources)
        
        self._page.add_init_script("delete navigator.__proto__.webdriver;")
        self._page.set_default_timeout(self._scraper.navigation_timeout_ms)

    def close(self) -> None:
        logger.info("Closing persistent Playwright browser session...")
        if self._page:
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def _paginate(
        self,
        page: Any,
        start_url: str,
        subreddit: str,
        max_pages: int,
    ) -> Iterator[tuple[list[ScrapedPost], str]]:
        delay = self._scraper.page_delay_seconds
        url = start_url
        pages_fetched = 0

        while url and pages_fetched < max_pages:
            logger.info("Fetching listing %s", url)
            page.goto(url, wait_until="domcontentloaded")
            html = page.content()
            posts = parse_listing_page(html, subreddit, self._scraper.base_url)
            pages_fetched += 1
            yield posts, html

            next_url = find_next_page_url(html, self._scraper.base_url)
            if not next_url:
                break
            url = next_url
            time.sleep(delay)

    def _launch_browser(self, playwright: Any) -> Any:
        browser_name = self._scraper.browser
        headless = self._scraper.headless
        browser_type = getattr(playwright, browser_name)
        try:
            return browser_type.launch(headless=headless)
        except Exception as exc:
            logger.warning("Standard browser launch failed: %s. Attempting fallback to system Chrome...", exc)
            try:
                return browser_type.launch(headless=headless, channel="chrome")
            except Exception as exc2:
                logger.warning("Fallback to system Chrome failed: %s. Attempting fallback to system Edge...", exc2)
                return browser_type.launch(headless=headless, channel="msedge")

    def _iter_listing_pages_playwright(
        self,
        subreddit: str,
        listing: ListingConfig,
    ) -> Iterator[tuple[list[ScrapedPost], str]]:
        start_url = resolve_listing_start_url(
            self._scraper.base_url,
            subreddit,
            listing.type,
            time_filter=listing.time_filter,
            query=listing.query,
            sort=listing.sort,
        )
        limit = max_pages_for_listing(self._config, listing)

        self._ensure_browser()
        yield from self._paginate(self._page, start_url, subreddit, limit)

    def _fetch_listing_json_page(
        self,
        subreddit: str,
        listing: ListingConfig,
        after: str | None = None,
    ) -> tuple[list[ScrapedPost], str] | None:
        if self._json_blocked:
            return None
            
        from urllib.parse import quote_plus
        
        base_url = "https://www.reddit.com"
        
        if listing.type == "new":
            url = f"{base_url}/r/{subreddit}/new.json?limit=100"
        elif listing.type == "top":
            t = listing.time_filter or "year"
            url = f"{base_url}/r/{subreddit}/top.json?t={t}&limit=100"
        elif listing.type == "search":
            q = quote_plus(listing.query or "")
            sort = listing.sort or "relevance"
            t = listing.time_filter or "year"
            url = f"{base_url}/r/{subreddit}/search.json?q={q}&restrict_sr=on&sort={sort}&t={t}&limit=100"
        else:
            raise ValueError(f"Unsupported listing type: {listing.type}")
            
        if after:
            url = f"{url}&after={after}"
            
        try:
            logger.info("Attempting JSON API fetch: %s", url)
            data = self._session.get_json(url)
            
            children = data.get("data", {}).get("children", [])
            scraped_posts = []
            
            for child in children:
                p_data = child.get("data", {})
                if not p_data:
                    continue
                scraped_posts.append(
                    ScrapedPost(
                        id=p_data.get("id", ""),
                        subreddit=p_data.get("subreddit", subreddit),
                        title=p_data.get("title", ""),
                        selftext=p_data.get("selftext", ""),
                        score=p_data.get("score", 0),
                        created_utc=p_data.get("created_utc", 0.0),
                        url=normalize_scraped_url(p_data.get("url", ""), self._scraper.base_url)
                    )
                )
            
            html_repr = json.dumps(data)
            return scraped_posts, html_repr
        except Exception as exc:
            logger.warning("JSON API fetch failed for r/%s (%s): %s", subreddit, listing.type, exc)
            self._json_blocked = True
            return None

    def iter_listing_pages(
        self,
        subreddit: str,
        listing: ListingConfig,
    ) -> Iterator[tuple[list[ScrapedPost], str]]:
        json_failed = False
        after = None
        pages_fetched = 0
        limit = max_pages_for_listing(self._config, listing)
        
        while pages_fetched < limit:
            if self._json_blocked:
                json_failed = True
                break
                
            delay = self._scraper.page_delay_seconds * random.uniform(0.8, 1.5)
            logger.info("Sleeping for %.2f seconds before next JSON API request...", delay)
            time.sleep(delay)
            
            res = self._fetch_listing_json_page(subreddit, listing, after)
            if res is None:
                json_failed = True
                break
                
            scraped_posts, html_repr = res
            yield scraped_posts, html_repr
            pages_fetched += 1
            
            try:
                data = json.loads(html_repr)
                after = data.get("data", {}).get("after", None)
            except Exception:
                after = None
                
            if not after:
                break
                
        if json_failed:
            logger.warning("JSON API fetch failed or was blocked. Falling back to Playwright browser scraper for r/%s (%s)...", subreddit, listing.type)
            yield from self._iter_listing_pages_playwright(subreddit, listing)

    def _fetch_post_json(self, post_url: str) -> str | None:
        if self._json_blocked:
            return None
        try:
            url = post_url.rstrip("/")
            if not url.endswith(".json"):
                url = url.replace("old.reddit.com", "www.reddit.com") + ".json"
            
            logger.info("Attempting post JSON API fetch: %s", url)
            data = self._session.get_json(url)
            
            if isinstance(data, list) and len(data) > 0:
                children = data[0].get("data", {}).get("children", [])
                if children:
                    p_data = children[0].get("data", {})
                    return p_data.get("selftext", "")
            return None
        except Exception as exc:
            logger.warning("Post JSON fetch failed for %s: %s", post_url, exc)
            self._json_blocked = True
            return None

    def _enrich_full_post_content_playwright(self, posts: list[Any]) -> tuple[list[Any], dict[str, int]]:
        stats = {"attempted": 0, "enriched": 0, "unchanged": 0, "failed": 0, "empty_body": 0}
        delay = self._scraper.page_delay_seconds
        enriched: list[Any] = []

        self._ensure_browser()
        page = self._page

        for post in posts:
            stats["attempted"] += 1
            try:
                logger.info("Fetching full post %s via Playwright", post.url)
                page.goto(post.url, wait_until="domcontentloaded")
                full_text = parse_post_detail_page(page.content())
                if not full_text:
                    stats["empty_body"] += 1
                    enriched.append(post)
                    continue

                merged = merge_selftext(post.selftext, full_text)
                if merged != post.selftext:
                    stats["enriched"] += 1
                    enriched.append(replace(post, selftext=merged))
                else:
                    stats["unchanged"] += 1
                    enriched.append(post)
            except Exception as exc:
                logger.warning("Failed Playwright fetch for post %s: %s", post.url, exc)
                stats["failed"] += 1
                enriched.append(post)

            time.sleep(delay)

        return enriched, stats

    def enrich_full_post_content(self, posts: list[Any]) -> tuple[list[Any], dict[str, int]]:
        stats = {"attempted": 0, "enriched": 0, "unchanged": 0, "failed": 0, "empty_body": 0}

        if not self._config.fetch_full_post_content or not posts:
            return posts, stats

        enriched: list[Any] = []
        playwright_fallback_posts: list[Any] = []

        # 1. Attempt Primary Collection Method (JSON API)
        for post in posts:
            stats["attempted"] += 1
            
            # OPTIMIZATION: Only enrich Reddit text threads (URLs containing /comments/)
            if "/comments/" not in post.url:
                stats["unchanged"] += 1
                enriched.append(post)
                continue
            
            if self._json_blocked:
                playwright_fallback_posts.append(post)
                continue
                
            # Randomized delay between requests to simulate human-like activity
            delay = self._scraper.page_delay_seconds * random.uniform(0.8, 1.5)
            logger.info("Sleeping for %.2f seconds before next JSON API request...", delay)
            time.sleep(delay)
            
            full_text = self._fetch_post_json(post.url)
            
            if full_text is not None:
                # JSON retrieval succeeded!
                if not full_text:
                    stats["empty_body"] += 1
                    enriched.append(post)
                    continue

                merged = merge_selftext(post.selftext, full_text)
                if merged != post.selftext:
                    stats["enriched"] += 1
                    enriched.append(replace(post, selftext=merged))
                else:
                    stats["unchanged"] += 1
                    enriched.append(post)
            else:
                # JSON retrieval failed, mark for Playwright fallback
                logger.warning("JSON post fetch failed. Marking post for Playwright fallback: %s", post.url)
                playwright_fallback_posts.append(post)

        # 2. Browser Fallback (Playwright) — only for failed posts
        if playwright_fallback_posts:
            logger.warning("Executing Playwright browser fallback for %d failed posts...", len(playwright_fallback_posts))
            fallback_enriched, fallback_stats = self._enrich_full_post_content_playwright(playwright_fallback_posts)
            
            enriched.extend(fallback_enriched)
            stats["enriched"] += fallback_stats["enriched"]
            stats["unchanged"] += fallback_stats["unchanged"]
            stats["failed"] += fallback_stats["failed"]
            stats["empty_body"] += fallback_stats["empty_body"]
            
        return enriched, stats


class MockListingScraper:
    """Test double: listing pages + optional post-detail bodies by post id."""

    def __init__(
        self,
        pages: dict[tuple[str, ...], list[str]],
        post_details: dict[str, str] | None = None,
        *,
        fetch_full: bool = True,
    ) -> None:
        self._pages = pages
        self._post_details = post_details or {}
        self._fetch_full = fetch_full

    def iter_listing_pages(
        self,
        subreddit: str,
        listing: ListingConfig,
    ) -> Iterator[tuple[list[ScrapedPost], str]]:
        key = _mock_page_key(subreddit, listing)
        html_pages = self._pages.get(key, [])
        base = "https://old.reddit.com"
        for html in html_pages:
            posts = parse_listing_page(html, subreddit, base)
            yield posts, html

    def enrich_full_post_content(self, posts: list[Any]) -> tuple[list[Any], dict[str, int]]:
        stats = {"attempted": 0, "enriched": 0, "unchanged": 0, "failed": 0, "empty_body": 0}
        if not self._fetch_full:
            return posts, stats

        enriched: list[Any] = []
        for post in posts:
            stats["attempted"] += 1
            detail_html = self._post_details.get(post.id)
            if not detail_html:
                enriched.append(post)
                stats["unchanged"] += 1
                continue

            full_text = parse_post_detail_page(detail_html)
            if not full_text:
                stats["empty_body"] += 1
                enriched.append(post)
                continue

            merged = merge_selftext(post.selftext, full_text)
            if merged != post.selftext:
                stats["enriched"] += 1
                enriched.append(replace(post, selftext=merged))
            else:
                stats["unchanged"] += 1
                enriched.append(post)

        return enriched, stats

    def close(self) -> None:
        pass


def create_listing_scraper(
    config: CollectionConfig,
    scraper: ListingScraper | None = None,
) -> ListingScraper:
    if scraper is not None:
        return scraper
    if config.scraper.engine == "playwright":
        return PlaywrightListingScraper(config)
    raise ValueError(f"Unsupported scraper engine: {config.scraper.engine}")
