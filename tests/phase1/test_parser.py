from __future__ import annotations

from pathlib import Path

from phase1.parser import (
    build_listing_url,
    build_search_url,
    find_next_page_url,
    merge_selftext,
    parse_listing_page,
    parse_post_detail_page,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_build_listing_urls():
    assert build_listing_url("https://old.reddit.com", "ChatGPT", "new").endswith("/r/ChatGPT/new/")
    assert "t=year" in build_listing_url("https://old.reddit.com", "ChatGPT", "top", time_filter="year")


def test_build_search_url():
    url = build_search_url(
        "https://old.reddit.com",
        "ChatGPT",
        "hallucination",
        time_filter="year",
        sort="relevance",
    )
    assert "/r/ChatGPT/search" in url
    assert "restrict_sr=on" in url
    assert "q=hallucination" in url
    assert "t=year" in url
    assert "sort=relevance" in url

    via_listing = build_listing_url(
        "https://old.reddit.com",
        "ChatGPT",
        "search",
        query="lost trust in ChatGPT",
        time_filter="year",
    )
    assert "lost+trust" in via_listing or "lost%20trust" in via_listing


def test_parse_listing_page():
    html = (FIXTURES / "listing_new.html").read_text(encoding="utf-8")
    posts = parse_listing_page(html, "ChatGPT", "https://old.reddit.com")
    assert len(posts) == 2
    assert posts[0].id == "abc111"
    assert posts[0].score == 120
    assert "plugins" in posts[0].selftext.lower()
    assert posts[0].url.startswith("https://old.reddit.com")


def test_parse_post_detail_page():
    html = (FIXTURES / "post_detail_abc111.html").read_text(encoding="utf-8")
    body = parse_post_detail_page(html)
    assert "confidently wrong" in body
    assert "hallucination" in body
    assert "lost trust" in body
    assert len(body) > 100


def test_merge_selftext_prefers_longer_full_body():
    listing = "Short excerpt."
    full = "Short excerpt.\n\nMuch longer full post with evidence about trust and consequences."
    assert len(merge_selftext(listing, full)) > len(listing)


def test_find_next_page_url():
    html = (FIXTURES / "listing_new.html").read_text(encoding="utf-8")
    nxt = find_next_page_url(html, "https://old.reddit.com")
    assert nxt is not None
    assert "after=t3_abc222" in nxt
