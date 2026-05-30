from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_POST_ID_RE = re.compile(r"^t3_([a-z0-9]+)$", re.I)


@dataclass(frozen=True)
class ScrapedPost:
    id: str
    subreddit: str
    title: str
    selftext: str
    score: int
    created_utc: float
    url: str


def _parse_score(score_el: Any) -> int:
    if score_el is None:
        return 0
    title_attr = score_el.get("title")
    if title_attr and title_attr.isdigit():
        return int(title_attr)
    text = score_el.get_text(strip=True)
    if text in ("•", "·", ""):
        return 0
    text = text.replace(",", "")
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    if text.isdigit():
        return int(text)
    return 0


def _parse_timestamp(thing: Any) -> float:
    time_el = thing.select_one("time[datetime]")
    if time_el and time_el.get("datetime"):
        raw = time_el["datetime"].replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw).timestamp()
        except ValueError:
            pass
    title_attr = time_el.get("title") if time_el else None
    if title_attr:
        for fmt in ("%a %b %d %H:%M:%S %Y UTC", "%Y-%m-%d %H:%M:%S %Z"):
            try:
                return datetime.strptime(title_attr, fmt).replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                continue
    return datetime.now(timezone.utc).timestamp()


def _extract_post_id(thing: Any) -> str | None:
    fullname = thing.get("data-fullname") or thing.get("id", "")
    match = _POST_ID_RE.match(fullname)
    if match:
        return match.group(1)
    if fullname.startswith("thing_t3_"):
        return fullname.replace("thing_t3_", "")
    link = thing.select_one("a.title")
    if link and link.get("href"):
        parts = link["href"].rstrip("/").split("/")
        if "comments" in parts:
            idx = parts.index("comments")
            if idx + 1 < len(parts):
                return parts[idx + 1]
    return None


def _extract_selftext(thing: Any) -> str:
    body = thing.select_one(".expando .usertext-body .md, .search-result-body .md")
    if body:
        return body.get_text("\n", strip=True)
    return ""


def _is_removed(title: str, selftext: str, tagline: str) -> bool:
    combined = f"{title} {selftext} {tagline}".lower()
    if "[removed]" in combined or "[deleted]" in combined:
        return True
    if "deleted" in tagline.lower() and "by" in tagline.lower():
        return True
    return False


def build_search_url(
    base_url: str,
    subreddit: str,
    query: str,
    *,
    time_filter: str = "year",
    sort: str = "relevance",
) -> str:
    """r/ChatGPT search URL (restrict_sr=on), scoped to subreddit."""
    from urllib.parse import quote_plus

    sub = subreddit.strip("/")
    q = quote_plus(query)
    return (
        f"{base_url.rstrip('/')}/r/{sub}/search"
        f"?q={q}&restrict_sr=on&sort={sort}&t={time_filter}"
    )


def build_listing_url(
    base_url: str,
    subreddit: str,
    listing: str,
    *,
    time_filter: str | None = None,
    query: str | None = None,
    sort: str | None = None,
    after: str | None = None,
) -> str:
    sub = subreddit.strip("/")
    if listing == "new":
        path = f"/r/{sub}/new/"
        url = f"{base_url.rstrip('/')}{path}"
    elif listing == "top":
        t = time_filter or "year"
        path = f"/r/{sub}/top/?t={t}"
        url = f"{base_url.rstrip('/')}{path}"
    elif listing == "search":
        if not query:
            raise ValueError("search listing requires query")
        url = build_search_url(
            base_url,
            subreddit,
            query,
            time_filter=time_filter or "year",
            sort=sort or "relevance",
        )
    else:
        raise ValueError(f"Unsupported listing: {listing}")

    if after:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}after=t3_{after}"
    return url


def resolve_listing_start_url(
    base_url: str,
    subreddit: str,
    listing_type: str,
    *,
    time_filter: str | None = None,
    query: str | None = None,
    sort: str | None = None,
) -> str:
    return build_listing_url(
        base_url,
        subreddit,
        listing_type,
        time_filter=time_filter,
        query=query,
        sort=sort,
    )


def parse_listing_page(html: str, subreddit: str, base_url: str) -> list[ScrapedPost]:
    """Parse an old.reddit.com listing HTML page into posts."""
    soup = BeautifulSoup(html, "html.parser")
    posts: list[ScrapedPost] = []

    for thing in soup.select("div.thing.link, div.search-result"):
        post_id = _extract_post_id(thing)
        if not post_id:
            continue

        title_el = thing.select_one("a.title, a.search-title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        url = normalize_scraped_url(href, base_url)

        tagline = thing.select_one("p.tagline, .search-result-meta")
        tagline_text = tagline.get_text(" ", strip=True) if tagline else ""
        selftext = _extract_selftext(thing)

        if _is_removed(title, selftext, tagline_text):
            continue

        score = _parse_score(thing.select_one("div.score, .search-score"))
        created_utc = _parse_timestamp(thing)

        posts.append(
            ScrapedPost(
                id=post_id,
                subreddit=subreddit,
                title=title,
                selftext=selftext,
                score=score,
                created_utc=created_utc,
                url=url,
            )
        )

    return posts


def find_next_page_url(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("span.nextprev a"):
        rel = link.get("rel") or []
        if "nofollow next" in " ".join(rel) or "next" in rel:
            href = link.get("href")
            if href:
                return urljoin(base_url + "/", href)
    return None


def merge_selftext(listing_selftext: str, full_selftext: str) -> str:
    """Prefer the longer non-empty body (listing excerpts vs full post page)."""
    listing = listing_selftext.strip()
    full = full_selftext.strip()
    if not full:
        return listing
    if not listing:
        return full
    return full if len(full) >= len(listing) else listing


def parse_post_detail_page(html: str) -> str:
    """Extract complete OP selftext from an old.reddit.com post (comments) page."""
    soup = BeautifulSoup(html, "html.parser")

    selectors = [
        "div.thing.link.self .usertext-body .md",
        "div.thing.link .usertext-body .md",
        ".entry .usertext-body .md",
        "form.usertext .usertext-body .md",
    ]
    for selector in selectors:
        body = soup.select_one(selector)
        if body:
            text = body.get_text("\n", strip=True)
            if text and text not in ("[removed]", "[deleted]"):
                return text
    return ""


def normalize_scraped_url(href: str, base_url: str) -> str:
    if href.startswith("http"):
        return href
    return urljoin(base_url.rstrip("/") + "/", href.lstrip("/"))
