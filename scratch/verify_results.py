import json
from pathlib import Path
from datetime import datetime, timezone

raw_dir = Path("c:/Users/user/REDDIT ANALYSER/data/raw")
manifest_path = raw_dir / "collection_manifest.json"

print("--- Data Raw Folder Check ---")
if not raw_dir.exists():
    print("Error: data/raw directory does not exist!")
    exit(1)

# Find post files
post_files = list(raw_dir.glob("posts_*.json"))
if not post_files:
    print("Error: No posts_*.json files found!")
    exit(1)

latest_posts_file = max(post_files, key=lambda f: f.stat().st_mtime)
print(f"Latest posts file: {latest_posts_file.name}")

# Read posts
with open(latest_posts_file, "r", encoding="utf-8") as f:
    posts = json.load(f)

print(f"Total raw posts collected: {len(posts)}")

# Read manifest
if manifest_path.exists():
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print("Manifest file found!")
    print(f"Manifest Run ID: {manifest.get('run_id')}")
    print(f"Manifest Post Count: {manifest.get('post_count')}")
    print(f"Manifest Max Posts Cap: {manifest.get('max_posts_cap')}")
    print(f"Manifest Fetch Full Post Content: {manifest.get('fetch_full_post_content')}")
    print(f"Manifest Scraper Headless: {manifest.get('scraper', {}).get('headless')}")
    print(f"Full Content Enrichment Stats: {manifest.get('full_content_stats')}")
else:
    print("Warning: collection_manifest.json not found!")

# Audit posts
subreddits = set()
min_date = float("inf")
max_date = float("-inf")
enriched_count = 0
empty_body_count = 0
link_post_count = 0

for p in posts:
    subreddits.add(p.get("subreddit"))
    ts = p.get("created_utc", 0.0)
    if ts < min_date:
        min_date = ts
    if ts > max_date:
        max_date = ts
    
    url = p.get("url", "")
    selftext = p.get("selftext", "")
    
    if "/comments/" not in url:
        link_post_count += 1
    else:
        if selftext:
            enriched_count += 1
        else:
            empty_body_count += 1

print("\n--- Dataset Audit Results ---")
print(f"Subreddits represented: {list(subreddits)}")
print(f"Is r/ChatGPT exclusive? {list(subreddits) == ['ChatGPT']}")

date_floor = datetime.fromisoformat(manifest.get("date_floor_utc").replace("Z", "+00:00")) if manifest else None
min_dt = datetime.fromtimestamp(min_date, tz=timezone.utc)
max_dt = datetime.fromtimestamp(max_date, tz=timezone.utc)

print(f"Earliest post date: {min_dt.isoformat()}")
print(f"Latest post date: {max_dt.isoformat()}")
if date_floor:
    print(f"Date Floor (9 months back): {date_floor.isoformat()}")
    print(f"All posts within 9-month window? {min_dt >= date_floor}")

print(f"\nLink posts (skipped enrichment): {link_post_count} ({link_post_count/len(posts)*100:.1f}%)")
text_posts = len(posts) - link_post_count
print(f"Text posts (comments threads): {text_posts} ({text_posts/len(posts)*100:.1f}%)")
print(f"Enriched text posts: {enriched_count} ({enriched_count/text_posts*100:.1f}% of text posts)")
print(f"Empty body text posts: {empty_body_count} ({empty_body_count/text_posts*100:.1f}% of text posts)")
