# Phase 1 — Reddit collection (Playwright)

Collects posts from **r/ChatGPT** (last **9 months**) via **browser scraping** on old.reddit.com.

## Collection sources

1. **`/r/ChatGPT/new/`** — paginate until posts are older than 9 months  
2. **`/r/ChatGPT/top/?t=year`** — top posts (filtered to 9 months)  
3. **Keyword search** — 16 research queries (`search_queries` in `config.yaml`)  
4. **Full post bodies** — **always on** (`fetch_full_post_content: true`): opens each post URL and stores complete `selftext`

Posts are **deduplicated by id** across all sources.

## Config

```yaml
collection:
  fetch_full_post_content: true   # required — research quality over scraping speed
```

## Stored fields

`id`, `subreddit`, `title`, `selftext`, `score`, `created_utc`, `url`

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
python -m phase1
```

**Policy:** Full-body fetch is **required** for this project. Expect longer collection runs; evidence quality for trust/hallucination/consequence analysis takes priority over speed.

## Tests

```bash
python -m pytest tests/phase1 -v -m "not integration"
```
