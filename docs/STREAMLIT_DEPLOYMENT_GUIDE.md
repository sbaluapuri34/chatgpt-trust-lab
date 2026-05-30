# Streamlit Deployment Guide
*ChatGPT Output Trust & Evaluation Lab*

This guide details the step-by-step procedure to deploy the ChatGPT Trust Lab dashboard to Streamlit Community Cloud, ensuring a public-facing URL and full database explorer functionality.

---

## 📦 GitHub Preparation Steps

To deploy the dashboard, prepare a clean GitHub repository containing only the files required to run the dashboard. This prevents exposing developer scrapers, keys, or credentials.

### 1. Files to Include (Committed to Git)
Commit the following files and directories:
```
.
├── app.py
├── config.yaml
├── requirements.txt
├── runtime.txt
├── phase3/
│   ├── __init__.py
│   └── config.py
├── phase5/
│   ├── __init__.py
│   └── dashboard.py
└── data/
    ├── aggregated/
    │   ├── theme_prevalence.csv
    │   ├── theme_cooccurrence.json
    │   ├── trust_erosion_report.json
    │   ├── severity_distribution.csv
    │   ├── score_impact.csv
    │   ├── representative_quotes.json
    │   └── methodology_snippet.json
    └── research.db
```

### 2. Files to Exclude (Do NOT Commit)
Do **not** commit the following directories and files. Add them to `.gitignore`:
- `phase1/` (Scrapers and collection engines)
- `phase2/` (Preprocessing scripts)
- `phase3/` (LLM analysis modules except config files)
- `scripts/` (Pipeline automation: ingestion, relabeling)
- `tests/` (Pytest test suite)
- `scratch/` (One-off scratch scripts)
- `.venv/` (Local Python environment)
- `.env` (Secret files and API keys)
- `.pytest_cache/` (Pytest run caches)

### 3. Recommended `.gitignore`
Create or update `.gitignore` in your repository:
```gitignore
# Python cache
__pycache__/
*.py[cod]
*$py.class

# Environments
.venv/
env/
venv/
ENV/

# Sensitive Config
.env

# Cache & Tests
.pytest_cache/
.coverage
htmlcov/

# Pipeline Folders to Exclude
phase1/
phase2/
scripts/
tests/
scratch/
data/raw/
data/batches/
data/backups/
data/*_test.db
```

---

## 🛠️ Deployment Configuration Files

### 1. `requirements.txt` Verification
Ensure the following packages are present in your `requirements.txt` (which is already configured):
```text
PyYAML>=6.0.1
streamlit>=1.32.0
pandas>=2.2.0
plotly>=5.19.0
```
*(Streamlit Community Cloud automatically installs all packages listed in `requirements.txt` before launching).*

### 2. `runtime.txt` Requirements
Create a file named `runtime.txt` in the root of your repository to specify the Python engine version:
```text
python-3.11
```

---

## 🚀 Deployment Instructions (Streamlit Community Cloud)

Follow these steps to deploy the application:

1. **Push Code**: Push the prepared files to a public GitHub repository.
2. **Log In**: Go to [Streamlit Community Cloud](https://share.streamlit.io/) and log in with your GitHub account.
3. **New App**: Click the **"New app"** button.
4. **Configure Settings**:
   - **Repository**: Select your repository (e.g., `username/chatgpt-trust-lab`).
   - **Branch**: Select the branch name (e.g., `main`).
   - **Main file path**: Enter `app.py`.
   - **App URL**: Choose a custom subdomain (e.g., `chatgpt-trust-lab`).
5. **Secrets & Environment Variables**:
   - The application does not require any active environment variables or database credentials since SQLite (`data/research.db`) is packed locally inside the git commit.
6. **Launch**: Click **"Deploy!"**.

Streamlit will provision a container, install dependencies from `requirements.txt`, and boot the server in about 1-2 minutes. Once finished, your dashboard will be live at `https://<subdomain>.streamlit.app` and accessible to anyone with the URL.
