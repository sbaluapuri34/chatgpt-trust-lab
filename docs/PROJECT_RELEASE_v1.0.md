# Project Release Notes — v1.0
*ChatGPT Output Trust & Evaluation Lab (ChatGPT Trust Lab)*

**Status**: Research Complete
**Release Version**: v1.0
**Date**: May 30, 2026

---

## 📊 Dataset Statistics
The project analyzed raw posts scraped from `r/ChatGPT` covering a 9-month temporal horizon. The data pipeline filtered, analyzed, and aggregated the posts through a two-stage hybrid workflow:

| Pipeline Funnel Stage | Post Count | Conversion / Filter Rate |
| :--- | :--- | :--- |
| **Total Ingested Raw Posts** | 1,091 | 100.0% (Initial corpus size) |
| **Preselected Keyword Candidates** | 729 | 66.8% (Deterministic pre-screening) |
| **Stage 1 Confirmed Relevant Posts** | 594 | 54.4% (Confirmed by LLM) |
| **Stage 2 Deep Theme Analyzed Posts** | 594 | 54.4% (Semantic primary theme assigned) |

---

## 📈 Final Theme Counts & Prevalence
Of the 594 confirmed relevant posts, the distribution across the 6 core research themes is as follows:

| Research Theme | Raw Count | Raw Prevalence | Weighted Count | Weighted Prevalence |
| :--- | :--- | :--- | :--- | :--- |
| **Confidently Incorrect Outputs** | 185 | 31.14% | 292.91 | 24.31% |
| **Real-World Impact of AI Outputs** | 131 | 22.05% | 318.07 | 26.40% |
| **User Evaluation & Verification Behavior** | 87 | 14.65% | 115.82 | 9.61% |
| **Over-Reliance on AI Outputs** | 73 | 12.29% | 156.51 | 12.99% |
| **User Trust Breakdown** | 72 | 12.12% | 222.27 | 18.45% |
| **Persuasive Outputs & Trust Formation** | 46 | 7.74% | 99.38 | 8.25% |
| **Total** | **594** | **100.00%** | **1,205.00** | **100.00%** |

*Note: Weighted counts adjust for community engagement using $\ln(1 + \max(\text{score}, 0))$ to highlight virally amplified community narratives.*

---

## ⚙️ Methodology Summary
The ChatGPT Trust Lab employs a structured two-stage hybrid methodology:

1. **Scraping & Ingestion (Phase 1)**: Ingests 1,091 raw posts from `r/ChatGPT` using keyword search queries and chronological listings to target trust calibration, hallucinations, and real-world consequences.
2. **Deterministic Pre-screening (Phase 2)**: Screens posts for keyword indicator categories (Confidence, Hallucinations, Trust, Trust Loss, Consequences). Posts are scored based on keyword density and upvotes. The top 729 posts are selected as candidates.
3. **LLM Deep Analysis (Phase 3)**: Candidates are processed in batches using `llama-3.1-8b-instant` (via Groq) to evaluate relevance, assign primary/secondary themes, classify severity (high, medium, low), extract verbatim evidence quotes, and document analytical rationales.
4. **Data Aggregation (Phase 4)**: Compiles the confirmed database records into structured insights (`theme_prevalence.csv`, `theme_cooccurrence.json`, `severity_distribution.csv`, `score_impact.csv`, `monthly_theme_trends.csv`). Curates top representative quotes programmatically based on classification confidence, keyword similarity, and rationale length, reducing Reddit upvote score to a minor tiebreaker.
5. **Interactive Visualization (Phase 5)**: Renders the compiled insights and the full qualitative database explorer in a dark-mode Streamlit dashboard.

---

## 🚀 Deployment Instructions

### Dashboard URL Placeholder
The live public dashboard is deployed at:
**`https://chatgpt-trust-lab.streamlit.app`**

### Steps to Deploy Externally:
1. **Create GitHub Repository**: Commit the required runtime files (`app.py`, `config.yaml`, `requirements.txt`, `runtime.txt`, `phase3/config.py`, `phase5/dashboard.py`, `data/aggregated/*`, and `data/research.db`).
2. **Log In to Streamlit**: Log in to [Streamlit Community Cloud](https://share.streamlit.io/) with your GitHub credentials.
3. **Deploy App**: Link the repository, specify `app.py` as the main entry point, and select Python 3.11 (`runtime.txt`).
4. **Launch**: Click **Deploy**. The application will compile and be publicly accessible.

*(For detailed instructions, refer to [docs/STREAMLIT_DEPLOYMENT_GUIDE.md](file:///c:/Users/user/REDDIT%20ANALYSER/docs/STREAMLIT_DEPLOYMENT_GUIDE.md)).*

---

## ⏳ Version History
- **v0.1**: Initial scraper pipeline and raw data ingestion.
- **v0.2**: Preprocessing heuristics and LLM batch classification setup.
- **v0.3**: SQLite database schema setup, taxonomy migration, and relabeling.
- **v0.4**: Rebranded platform to *ChatGPT Output Trust & Evaluation Lab* and restructured visual selectors to follow the sequential user journey.
- **v0.5**: Designed and implemented the programmatic qualitative re-ranking scoring formula for evidence quotes (capping keyword similarity and penalizing fictional/meta posts).
- **v1.0**: Audited representative quotes (exchanged the positive custody outcome for a developer ban consequence) and confirmed 100% database/aggregation lock. **Research complete.**

---

## ⚠️ Known Limitations
1. **Self-Selection Bias**: Sourced from `r/ChatGPT`, which naturally attracts users seeking tech support, sharing errors/memes, or complaining. Severe consequences and trust breakdowns are likely over-represented compared to general user behavior.
2. **Thread Boundary**: Only main posts are analyzed; comments are excluded. Some contextual verification behaviors occurring in thread comments may be missed.
3. **Classifier Limits**: Llama 3.1 8B is used for primary/secondary theme assignment. Edge cases with ambiguous wording may exhibit minor classification deviations.
4. **Temporal Horizon**: The dataset covers a 9-month timeframe ending in late 2025/2026. Rapid model upgrades post-release may alter the distribution of confidently incorrect outputs.
