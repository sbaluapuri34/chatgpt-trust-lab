# Local Deployment Guide — ChatGPT Output Trust & Evaluation Lab

This guide outlines the step-by-step procedure to deploy, configure, and execute the **ChatGPT Output Trust & Evaluation Lab** (ChatGPT Trust Lab) on a fresh Windows PC.

---

## 1. Prerequisites

### Python Environment
*   **Required Python Version**: Python **3.12 or higher** is required (successfully verified and tested on **Python 3.14.4**).
*   **Installation Tip**: Ensure **"Add Python to PATH"** is selected during the official installer wizard.

### Web Browser Control
*   The collection pipeline uses **Playwright** browser automation. You do not need a pre-installed Google Chrome browser, as Playwright installs its own sandboxed Chromium binary. However, fallbacks to system-installed Google Chrome and Microsoft Edge are fully supported.

---

## 2. Setup and Installation

Follow these steps in **PowerShell** or **Command Prompt** (run as standard user):

### Step 1: Create Virtual Environment
Navigate to the project root directory and initialize a virtual environment:
```powershell
python -m venv .venv
```

### Step 2: Activate Virtual Environment
*   **PowerShell**:
    ```powershell
    .venv\Scripts\Activate.ps1
    ```
    *(Note: If you receive a script execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first)*
*   **Command Prompt (cmd)**:
    ```cmd
    .venv\Scripts\activate.bat
    ```

### Step 3: Install Core Dependencies
Install the required packages from `requirements.txt`:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install Playwright Browser Binaries
Playwright requires its own managed Chromium browser binary to operate. Fetch and install it with:
```powershell
playwright install chromium
```

---

## 3. Configuration & Environment Variables

### The `.env` Configuration File
Create a file named `.env` in the root of the project (copying from `.env.example`). It must contain the following variables:

```ini
# Groq API Credentials (Primary LLM Engine)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Gemini API Credentials (Fallback LLM Engine)
GEMINI_API_KEY=your_gemini_api_key_here
```

### The `config.yaml` Settings
The pipeline behavior is declared in `config.yaml`. The key parameters for Phase 1 are:
*   `collection.subreddits`: Set to `[ChatGPT]` for research scoping.
*   `collection.months_back`: Set to `9` (the historical target window).
*   `collection.fetch_full_post_content`: Set to `true` (enforces full text body enrichment).
*   `collection.max_posts`: Caps total raw captures (default `1200`).
*   `scraper.page_delay_seconds`: Delay between scraping pages (e.g. `2.0` seconds to simulate human activity).

---

## 4. Execution Commands

**`PHASE_1_LOCKED = TRUE`** — Collection is complete. Do **not** run `collect.py` unless you explicitly need a new dataset.

Authoritative source: `data/raw/posts_20260529.json` (1,091 posts, validated).

### Recommended: run from Phase 2
```powershell
.\scripts\run_from_phase2.ps1
```

### Phase 1 (completed — locked)
Collection is **not** part of normal execution. Emergency re-collection only:
```powershell
python scripts/collect.py --allow-new-collection
```

### Phase 2: Ingest & preprocessing
```powershell
python scripts/ingest.py
python -m phase2.preprocess
python -m phase2.select_candidates
```
*   **Input**: locked `posts_20260529.json`
*   **Output**: `data/research.db`

### Phase 3: Two-stage LLM analysis (Groq)
```powershell
python scripts/run_relevance.py
python scripts/run_deep_analysis.py
```
*   **Requires**: `GROQ_API_KEY` in `.env`
*   **Output**: `data/batches/` + `post_analysis` table

### Phase 1 backup (recommended once)
```powershell
.\scripts\backup_phase1.ps1
```

### Phase 4: Streamlit Dashboard UI (Planned)
Launches the interactive analytical dashboard:
```powershell
streamlit run app.py
```

---

## 5. Expected Folder Structure

Once fully deployed and executed, the project workspace will match the following layout:

```
REDDIT ANALYSER/
├── .venv/                      # Python virtual environment
├── config.yaml                 # Scraper configuration & pipeline parameters
├── requirements.txt            # System dependency declarations
├── pytest.ini                  # Unit test runner configurations
├── .env                        # Private API credentials (ignored by Git)
├── .env.example                # Shared environment variable blueprint
├── data/
│   ├── raw/
│   │   ├── posts_YYYYMMDD.json         # Raw scraped & enriched posts
│   │   └── collection_manifest.json    # Provenance manifest & run metadata
│   ├── aggregated/             # Aggregated stats & CSV reporting
│   └── research.db             # Preprocessed SQLite database (Phase 2+)
├── docs/
│   ├── ARCHITECTURE.md         # Comprehensive structural specifications
│   ├── IMPLEMENTATION_PLAN.md  # Blueprint for current/planned phases
│   └── DEPLOYMENT_GUIDE.md     # This local deployment document
├── phase1/                     # Phase 1: Python source modules
│   ├── __init__.py
│   ├── __main__.py
│   ├── collector.py            # Collection orchestration & deduplication
│   ├── config.py               # YAML configuration model mappings
│   ├── parser.py               # old.reddit.com HTML parsing rules
│   └── playwright_scraper.py   # Playwright browser automation
├── scripts/
│   ├── collect.py              # CLI scraper entrypoint
│   └── run_phase1_tests.ps1    # Automated testing shortcut script
└── tests/
    └── phase1/                 # Phase 1 unit & integration test suites
```

---

## 6. Troubleshooting Guide

### 1. Playwright "Executable not found" Error
*   **Symptom**: `playwright._impl._errors.Error: Executable doesn't exist at C:\Users\...`
*   **Resolution**: Run `playwright install chromium` inside your active virtual environment.

### 2. Reddit HTTP 429 Too Many Requests (Rate Limiting)
*   **Symptom**: Log displays `Status: 429` during listing fetches.
*   **Resolution**: The pipeline automatically switches to browser automation and blocks non-critical resources (stylesheets/images) to speed up recovery. If persistent, increase `scraper.page_delay_seconds` to `3.0` or higher in `config.yaml` to lower request density.

### 3. ExecutionPolicy Error when Activating Virtual Environment
*   **Symptom**: `Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
*   **Resolution**: Open PowerShell and run:
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
    ```
    Then attempt activation again.

---

## 7. Deployment Validation Checklist

Before declaring the deployment complete, verify the environment using this checklist:

- [ ] **Dependency Check**: `pip list` contains `playwright`, `beautifulsoup4`, and `PyYAML`.
- [ ] **API Access**: `.env` contains valid credentials for Groq and Gemini.
- [ ] **Unit Tests**: Run pytest from the root:
    ```powershell
    pytest -v -m "not integration"
    ```
    *Expectation: 15 passed, 0 failed.*
- [ ] **Playwright Test**: Run the collection test script to verify browser launches:
    ```powershell
    python scripts/collect.py
    ```
    *Expectation: The process launches a headless browser, bypasses rate limiting, and successfully completes raw collection.*
- [ ] **Manifest Verification**: Inspect `data/raw/collection_manifest.json` and ensure `post_count` is populated and matches the configured collection targets.
