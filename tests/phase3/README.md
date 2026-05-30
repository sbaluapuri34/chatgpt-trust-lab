# Phase 3 tests

## Offline (no API keys)

```powershell
python -m pytest tests/phase3 -v -m "not integration"
```

Covers validation, batching, JSON parsing, and **mock** full pipeline on fixture posts.

## Live integration (Groq + Gemini)

Requires `.env`:

```
GROQ_API_KEY=...
GEMINI_API_KEY=...
```

```powershell
python -m pytest tests/phase3 -v -m integration
# or
.\scripts\run_phase3_tests.ps1
```

Uses 2 candidate posts from `tests/phase2/fixtures/sample_posts.json` (isolated temp DB; does not touch locked Phase 1 data).

## Test modules

| File | Purpose |
|------|---------|
| `test_validation.py` | Theme enum, quote substring rules |
| `test_batching.py` | Token batch planner |
| `test_json_parse.py` | LLM response JSON extraction |
| `test_pipeline_mock.py` | Full Stage 1 + 2 with MockLLMClient |
| `test_live_llm.py` | Groq/Gemini smoke + live pipeline |
