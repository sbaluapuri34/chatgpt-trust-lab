# Implementation Plan — ChatGPT Output Trust & Evaluation Lab

**Aligned with:** [`ARCHITECTURE.md`](ARCHITECTURE.md) v3.6  
**Status:** Phase 1 **locked & validated**; Phase 2–3 implemented; Phase 4–5 per plan below.

> **Phase 1 is a one-time collection step and has already been completed.** Subsequent development assumes `data/raw/posts_20260529.json` (1,091 posts) as the immutable input source. See [`PHASE_1_CHECKPOINT.md`](PHASE_1_CHECKPOINT.md).

---

## Research objective (implementation scope)

**Not in scope:** Analyzing every general discussion in r/ChatGPT.

**In scope:** Posts that substantively discuss ChatGPT (or comparable AI) communication, trust, reliability, verification, accountability, or consequences — analyzed using **seven research themes** (assigned in Stage 2 from full post text):

1. Confident but Incorrect Outputs  
2. User Trust Breakdown  
3. Over-Reliance on AI Outputs  
4. User Evaluation & Verification Behavior  
5. Real-World Impact of AI Outputs  
6. Persuasive Outputs & Trust Formation  
7. Needs Manual Review  

**Not final themes:** Phase 2 keyword categories (Confidence, Hallucinations, Trust, Trust Loss, Consequences) — supporting features for ranking and optional LLM hints only.

The pipeline achieves this by: **broad collection → deterministic preprocessing → candidate selection → two-stage LLM (full-text relevance → research-theme labeling) → weighted aggregation**.

---

## Pipeline overview (build order)

```
r/ChatGPT
  → Collect posts (9 months)
  → Preprocessing (keywords, no LLM)
  → Candidate selection (rank & cap)
  → LLM Stage 1 — Relevance filter
  → LLM Stage 2 — Research theme analysis (7 themes, full text)
  → Aggregation
  → Streamlit dashboard
```

---

## Phase map

| Phase | Script / module | Status | Output |
|-------|-----------------|--------|--------|
| **1** | `phase1/`, `scripts/collect.py` | **Done (v3.3 + full body)** | Raw JSON + manifest |
| **2a** | `scripts/ingest.py` | **Done** | SQLite `posts` |
| **2b** | `phase2/preprocess.py` | **Done** | `post_features` (keyword features only) |
| **2c** | `phase2/select_candidates.py` | **Done** | `is_candidate` flag + selection report |
| **3a** | `scripts/plan_batches.py` + `phase3/relevance.py` | **Done** (mock + live clients) | Stage 1 batch results |
| **3b** | `phase3/deep_analysis.py` | **Done** (mock + live clients) | Stage 2 batch results |
| **4** | `scripts/aggregate.py` | Planned | CSV/JSON aggregates |
| **5** | `app.py` | Planned | Streamlit dashboard |

---

## Phase 1 — Collect (r/ChatGPT only)

### Implementation tasks

- [x] Update `config.yaml`: single subreddit `ChatGPT`; keywords moved to `preprocessing` section  
- [x] `phase1/playwright_scraper.py` + `phase1/parser.py` (old.reddit.com HTML)  
- [x] Refactor `phase1/collector.py`: Playwright pagination until `created_utc < date_floor`  
- [x] Remove PRAW / Reddit API dependency  
- [x] Keyword search URLs (`search_queries` in config) with cross-source dedupe  
- [x] `fetch_full_post_content: true` (required, default on) — visit every post page; quality over speed  
- [x] Store: `id`, `title`, `selftext`, `score`, `created_utc`, `url`, `subreddit`  
- [x] No keyword filter at collection  
- [x] Update `tests/phase1/` for v3.0 contract  

### Exit criteria

- [x] Manifest shows `subreddits: ["ChatGPT"]` only  
- [x] `keyword_filter_at_collection: false` in manifest  
- [ ] Run `playwright install chromium` then live collection; record manifest with total N  

---

## Phase 2 — Ingest, preprocessing, candidate selection

### 2a — Ingest (`scripts/ingest.py`)

- [ ] Load raw JSON → SQLite `posts`  
- [ ] Compute `weight = ln(1 + max(score, 0))`  
- [ ] Build `text = title + "\n\n" + selftext`  

### 2b — Preprocessing (`phase2/preprocess.py`)

**No LLM.** For each post compute:

| Field | Description |
|-------|-------------|
| `text_length` | Character count of `text` |
| `keyword_match_count` | Total keyword hits (count duplicates or unique — document choice) |
| `match_confidence` | Hits in Confidence category |
| `match_hallucinations` | Hallucinations category |
| `match_trust` | Trust category |
| `match_trust_loss` | Trust Loss category |
| `match_consequences` | Consequences category |
| `category_hit_count` | Number of distinct categories with ≥1 hit |

Keywords per architecture §4 (fixed lists in `config.yaml`). These categories are **preprocessing signals only** — they must not be exported or charted as final research themes (see Phase 3).

### 2c — Candidate selection (`phase2/select_candidates.py`)

- [ ] `relevance_raw = keyword_match_count + 2 * category_hit_count` (configurable)  
- [ ] `rank_score = w_kw * norm(relevance_raw) + w_vote * norm(score)`  
- [ ] Mark `is_candidate = 1` for top **K** posts (config: e.g. 800–1500; tunable for budget)  
- [ ] Write `data/aggregated/candidate_selection_report.json` (N total, N candidates, thresholds)  

### Exit criteria

- ≥90% of LLM-bound posts have `keyword_match_count >= 1`  
- Candidate table documented in methodology  

---

## Phase 3 — Two-stage LLM (Groq primary, Gemini fallback)

### Design principles (v3.5)

| Principle | Implementation |
|-----------|----------------|
| **Full-text authority** | Both stages receive `posts.text` (`title` + `selftext`) as the primary input |
| **Keywords are hints** | `keyword_summary` from `post_features` is optional; prompts state it is non-binding |
| **Seven research themes** | Stage 2 `primary_theme` / `secondary_themes[]` use the fixed enum below — not Phase 2 category names |
| **No keyword→theme mapping** | Do not set `primary_theme` from `match_*` columns in code |

### Research theme enum (Stage 2)

| Slug | Display name |
|------|----------------|
| `overconfident_incorrect_outputs` | Confidently Incorrect Outputs |
| `user_trust_breakdown` | User Trust Breakdown |
| `over_reliance_on_ai_outputs` | Over-Reliance on AI Outputs |
| `user_evaluation_verification_behavior` | User Evaluation & Verification Behavior |
| `real_world_impact_of_ai_outputs` | Real-World Impact of AI Outputs |
| `persuasive_outputs_trust_formation` | Persuasive Outputs & Trust Formation |
| `needs_manual_review` | Needs Manual Review |

Store in `config.yaml` under `research_themes` for validation and prompt generation.

### Adaptive batching (both stages)

- Reuse token planner: **50–100 posts/request** until token budget  
- Separate batch plans: `data/batches/relevance/batch_plan.json`, `data/batches/deep/batch_plan.json`  
- Only `is_candidate = 1` posts enter Stage 1  
- Token budget must account for **full `text`** per post (Stage 2 needs more output tokens for `theme_rationale` + quote)

### Stage 1 — Relevance filter (`phase3/relevance.py`)

**Purpose:** Drop off-topic posts (memes, pure product news, unrelated tips) before paid theme labeling.

**Input per post:**

```json
{
  "id": "abc123",
  "text": "full title + selftext",
  "score": 42,
  "keyword_summary": {
    "keyword_match_count": 3,
    "match_confidence": 1,
    "match_hallucinations": 2,
    "match_trust": 0,
    "match_trust_loss": 0,
    "match_consequences": 0,
    "category_hit_count": 2
  }
}
```

`keyword_summary` is **optional** in the payload; when present, prompts must say: *use for context only; relevance must be decided from `text`.*

**Output per post:**

```json
{
  "id": "abc123",
  "relevant": true,
  "relevance_score": 0.82,
  "reason": "Discusses relying on a confident wrong answer with real harm."
}
```

**Tasks:**

- [x] `prompts/relevance_v1.txt` — scope = research program (seven themes), read full `text`  
- [x] `scripts/plan_batches.py` — pack by tiktoken on `text` (+ small overhead)  
- [x] Drop posts with `relevant = false` before Stage 2  
- [x] Cache `data/batches/relevance/batch_XXX_results.json`  
- [x] `post_analysis` table: `stage1_relevant`, `stage1_relevance_score`, `stage1_reason`

### Stage 2 — Research theme analysis (`phase3/deep_analysis.py`)

**Only** Stage 1 posts where `relevant = true`.

**Input per post:** Same as Stage 1 (`id`, `text`, `score`, optional `keyword_summary`).

**Output per post:**

```json
{
  "id": "abc123",
  "primary_theme": "overconfident_hallucinations",
  "secondary_themes": ["user_over_trust"],
  "theme_rationale": "One-sentence justification tied to the narrative.",
  "evidence_quote": "verbatim substring from text",
  "severity": "low|medium|high",
  "model_confidence": 0.88,
  "secondary_labels": ["medical_context"]
}
```

| Field | Rules |
|-------|--------|
| `primary_theme` | Required; must be a research theme slug from the enum |
| `secondary_themes` | 0–3 items; same enum; exclude duplicate of `primary_theme` |
| `theme_rationale` | Required; must align with `evidence_quote` |
| `evidence_quote` | Required; substring of `text` |
| `model_confidence` | 0–1 model self-score (not the Confidence keyword category) |
| `secondary_labels` | Optional tags; **excluded** from theme prevalence in Phase 4 |

**Tasks:**

- [x] `prompts/deep_analysis_v1.txt` — theme definitions, assignment rules, keyword hint disclaimer  
- [x] Validate enum + quote substring in Python before DB write  
- [x] Cache `data/batches/deep/batch_XXX_results.json`  
- [x] `post_analysis`: `primary_theme`, `secondary_themes` (JSON), `theme_rationale`, `evidence_quote`, `severity`, `model_confidence`

### SQLite columns (Phase 3 additions)

Suggested columns on `posts` or `post_analysis`:

- `stage1_relevant`, `stage1_relevance_score`, `stage1_reason`  
- `primary_theme`, `secondary_themes` (JSON text), `theme_rationale`  
- `evidence_quote`, `severity`, `model_confidence`  

Do **not** add columns that copy `match_*` into theme fields.

### Cost controls

- [x] Skip LLM if cache exists (`--force` to override)  
- [x] Gemini only on Groq failure per batch  
- [x] Log `data/batches/llm_usage.json` (model, stage, post count)  

### Exit criteria

- Stage 1 calls ≪ raw N (only candidates)  
- Stage 2 calls ≪ Stage 1 input (only relevant)  
- ≥90% valid `evidence_quote` substrings  
- 100% of `primary_theme` values in research theme enum  
- Document call counts + theme distribution in manifest  
- Methodology appendix lists **seven themes** separately from **five keyword categories**  

### Testing (deferred)

- [ ] Live Groq/Gemini integration tests when API keys are provided (`tests/phase3/README.md`)  

---

## Phase 4 — Aggregation (`scripts/aggregate.py`)

**Input themes:** Stage 2 `primary_theme` slugs only (seven research themes + `mixed_or_multitheme`). Do not aggregate Phase 2 `match_*` columns as themes.

- [ ] Raw + weighted counts per **research theme** (`primary_theme`)  
- [ ] Optional: secondary theme co-occurrence matrix (`secondary_themes`)  
- [ ] Trust erosion panel: `trust_erosion` theme prevalence; optional diagnostic cross-tab with `match_trust_loss` (labeled “preprocessing signal”)  
- [ ] Severity distribution (raw + weighted) by research theme  
- [ ] Score impact analysis (score decile × research theme)  
- [ ] Top evidence quotes per research theme (by `weight`)  
- [ ] `methodology_snippet.txt` — funnel table + distinction between keyword features and research themes  

---

## Phase 5 — Dashboard (`app.py`)

| Section | Data source |
|---------|-------------|
| Theme distribution | `theme_summary.csv` |
| Weighted theme distribution | weighted columns |
| Trust erosion metrics | `trust_erosion` research theme (+ optional keyword diagnostic) |
| Research theme distribution | seven-theme bar chart from Stage 2 only |
| Severity distribution | severity histogram |
| Reddit score impact | score-bin cross-tab |
| Evidence explorer | `posts` WHERE relevant + quote |
| Representative quotes | top by weight per theme |
| Final findings | optional on-demand Grok + template |

- [ ] Read-only SQLite; no LLM on filter change  
- [ ] Funnel diagram in sidebar (raw → candidates → S1 → S2)  

---

## Config changes (`config.yaml`)

```yaml
collection:
  subreddits: [ChatGPT]
  months_back: 9
  # no keyword filter at collection

preprocessing:
  keyword_categories: { ... }  # Phase 2 supporting features ONLY — not research themes

research_themes:
  - slug: overconfident_hallucinations
    label: Overconfident Hallucinations
  - slug: user_over_trust
    label: User Over-Trust
  # ... (all seven + mixed_or_multitheme) — see ARCHITECTURE.md Phase 3

selection:
  max_candidates: 1200
  w_keyword: 0.6
  w_score: 0.4

llm:
  primary: groq
  fallback: gemini
  batching: { ... }  # token limits
```

---

## Testing strategy

| Layer | Tests |
|-------|--------|
| Phase 1 | Mock Reddit listings; no keyword gate; single subreddit |
| Preprocessing | Keyword category counts on fixture posts (not theme labels) |
| Selection | Ranking order and top-K cut |
| LLM Stage 1 | Mock API; relevance from fixture `text` |
| LLM Stage 2 | Mock API; enum validation for seven research themes; quote substring check |
| Aggregation | SQL fixture DB → expected prevalences by **research theme** slug |
| Aggregation | SQL fixture DB → expected prevalences |

Run: `pytest tests/ -v -m "not integration"`

---

## Timeline (part-time)

| Week | Focus |
|------|--------|
| 1 | Fix Phase 1 + ingest + preprocess + select |
| 2 | Stage 1 + Stage 2 LLM + aggregate |
| 3 | Streamlit + write-up |

---

## Deliverables checklist

- [ ] Updated Phase 1 collector (ChatGPT-only, no collect-time keywords)  
- [ ] `research.db` with preprocessing + candidate flags  
- [ ] Stage 1 & 2 batch caches + usage log  
- [ ] Aggregated metrics + Streamlit app  
- [ ] Methodology section with cost funnel table  

---

## Document control

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Architecture | v3.0 |
| Last updated | 2026-05-29 |
