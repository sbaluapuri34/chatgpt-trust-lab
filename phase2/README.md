# Phase 2 — Ingest, preprocessing, candidate selection

Loads Phase 1 raw JSON into SQLite, scores posts against research keyword categories, and selects top-K candidates for LLM analysis.

## Pipeline

```powershell
python scripts/ingest.py
python -m phase2.preprocess
python -m phase2.select_candidates
```

Or run all steps:

```powershell
python -m phase2
```

## Outputs

| Artifact | Location |
|----------|----------|
| SQLite database | `data/research.db` |
| Selection report | `data/aggregated/candidate_selection_report.json` |

## Keyword matching

- Case-insensitive substring search on `text` (`title` + `selftext`)
- `keyword_match_count` = total occurrence counts across all keywords
- `category_hit_count` = number of categories with ≥1 hit
