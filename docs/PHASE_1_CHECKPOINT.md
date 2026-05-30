# Phase 1 checkpoint — locked dataset

**Status:** `PHASE_1_LOCKED = TRUE`  
**Date validated:** 2026-05-29

## Authoritative research dataset

| Artifact | Path |
|----------|------|
| Posts (1,091 unique) | `data/raw/posts_20260529.json` |
| Collection manifest | `data/raw/collection_manifest.json` |

**Scope:** r/ChatGPT only · last 9 months · full-body enrichment · validation complete.

## Policy

Phase 1 is a **one-time collection step** and has already been completed. Subsequent development assumes the existing validated dataset as the input source.

1. Do **not** rerun Phase 1 automatically.
2. Do **not** recollect Reddit data unless explicitly requested.
3. Do **not** overwrite, replace, regenerate, or delete the authoritative raw files.
4. All downstream work (Phase 2–5) reads from this dataset.
5. Code changes must remain backward compatible with `posts_20260529.json`.
6. Any change that would invalidate the collected dataset requires **explicit owner confirmation**.

## Pipeline entry point

```text
Phase 2 → Ingest / preprocessing / candidate selection
Phase 3 → LLM analysis (Groq primary, Gemini fallback)
Phase 4 → Aggregation
Phase 5 → Dashboard
```

```powershell
.\scripts\run_from_phase2.ps1
```

## Backup

Run after any manual edits to locked artifacts:

```powershell
.\scripts\backup_phase1.ps1
```

Backups are written to `data/backups/phase1_locked/<timestamp>/` and include raw data plus key documentation copies.

## Emergency new collection (owner only)

```powershell
python scripts/collect.py --allow-new-collection
```

This writes a **new** dated file; it does not replace `posts_20260529.json` unless you manually do so.
