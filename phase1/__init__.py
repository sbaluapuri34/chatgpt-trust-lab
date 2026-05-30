"""Phase 1: r/ChatGPT collection via Playwright (old.reddit.com)."""

from phase1.collector import PostCollector, collect_posts
from phase1.config import CollectionConfig, ListingConfig, ScraperConfig, load_config

__all__ = [
    "PostCollector",
    "collect_posts",
    "load_config",
    "CollectionConfig",
    "ListingConfig",
    "ScraperConfig",
]
