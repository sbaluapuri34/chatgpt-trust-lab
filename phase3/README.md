# Phase 3 — LLM relevance + research theme analysis

Two-stage pipeline for candidate posts (`is_candidate = 1`):

1. **Stage 1 (relevance)** — filter to on-topic posts using full `text`
2. **Stage 2 (deep)** — assign one of **seven research themes** (+ optional secondary themes)

**LLM:** Groq (primary) · Gemini (fallback per batch)

Phase 2 keyword columns are optional hints only. Requires Phase 2 complete on the locked Phase 1 dataset.

## Setup

```powershell
pip install -r requirements.txt
```

`.env`:

```
GROQ_API_KEY=...
GEMINI_API_KEY=...   # optional fallback
```

## Commands

```powershell
python scripts/run_relevance.py
python scripts/run_deep_analysis.py
python -m phase3
```

Or run the full downstream pipeline from Phase 2:

```powershell
.\scripts\run_from_phase2.ps1
```

## Outputs

| Artifact | Location |
|----------|----------|
| Batch results | `data/batches/{relevance,deep}/batch_*_results.json` |
| Usage log | `data/batches/llm_usage.json` |
| Analysis | `post_analysis` in `data/research.db` |
