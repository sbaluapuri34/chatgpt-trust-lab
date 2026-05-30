# Executive Summary: ChatGPT Trust Lab v1.0
**Project Title**: ChatGPT Output Trust & Evaluation Lab (ChatGPT Trust Lab)  
**Author**: Srish  
**Contact**: s.baluapuri34@gmail.com  
**Project Status**: Research & Analysis Complete  
**Date**: May 30, 2026  

---

### Executive Brief
Large Language Models (LLMs) like ChatGPT have achieved remarkable fluency, yet their tendancy to present factually incorrect outputs with high confidence (hallucinations) creates a dangerous gap in user trust. This project establishes the **ChatGPT Output Trust & Evaluation Lab**, an empirical investigation that moves beyond synthetic model benchmarks to analyze how real-world users actually interact with, verify, and calibrate their trust in ChatGPT.

By ingesting **1,091 unique posts** from the `r/ChatGPT` practitioner community, pre-screening **729 candidate threads**, and semantically mapping **594 relevant cases** through a two-stage LLM pipeline, this study provides a comprehensive taxonomy of user trust, caught hallucinations, and downstream consequences.

---

### What Was Done
1.  **Engineered an Automated Ingestion Pipeline (Phase 1)**: Sourced organic user narratives from `old.reddit.com` covering a 9-month window using Playwright browser automation.
2.  **Built Preprocessing Filters (Phase 2)**: Developed deterministic keyword density screening and upvote engagement heuristics to extract 729 relevance candidates.
3.  **Deployed a Two-Stage LLM Semantic Classifier (Phase 3)**: Processed candidate threads using `llama-3.1-8b-instant` via the Groq API (with Gemini fallback) to confirm relevance, identify primary/secondary themes, score severity (high, medium, low), and extract analytical rationales and verbatim evidence quotes.
4.  **Compiled Analytics Tables (Phase 4)**: Developed a log-scaled upvote weighting formula to adjust for community virality, built theme co-occurrence matrices, and structured representative quote ranking algorithms.
5.  **Launched an Auditing Dashboard (Phase 5)**: Implemented an interactive dark-mode dashboard in Streamlit containing metric diagnostics, Plotly charts, and a read-only qualitative database explorer.

---

### Key Research Findings
*   **The Prevalence Paradox**: While **Confidently Incorrect Outputs** represent the most common primary failure mode by raw count (185 posts, 31.14%), **Real-World Impact of AI Outputs** dominates the engagement-weighted share (318.07 weighted count, 26.40% weighted prevalence). Users are highly motivated to share and upvote threads detailing tangible consequences (medical auditing successes, legal brief fabrications, financial fraud discovery).
*   **Limits of Simple Keyword Matching**: A rigorous audit of deterministic screening rules revealed an **88.89% false positive rate** (precision of 11.11%) and a **60.0% false negative rate** (recall of 40.0%). Keyword rules are highly prone to context noise (e.g. negated keywords) and completely fail to capture implicit trust narratives (e.g. users describing professional termination without using the literal word "trust").
*   **Emotional Attachment vs. Auditing Rigor**: The study maps a deep community tension. A substantial portion of the community exhibits **Over-Reliance** (12.29%), treating the model as a companion or therapist. Conversely, highly skeptical professionals caught model hallucinations (such as fabricated papers or books) and developed sophisticated auditing behaviors (e.g., prompting for sources or creating "Closed-Loop Tribunals").
*   **Safety Filters and updates Suffer Trust Erosion**: **User Trust Breakdown** (12.12%) is heavily driven by OpenAI's platform adjustments. Inconsistent safety filters, unannounced model updates, and silent downgrades trigger immediate user frustration and trust loss.

---

### Why It Matters
*   **For Product Managers (PMs)**: Proves that users are highly sensitive to "sycophancy" (the model agreeing with errors) and unannounced behavioral shifts. Design patterns must shift from absolute conversational fluency to active, visible confidence calibration (e.g., the model communicating its own uncertainty).
*   **For Academic Evaluators**: Validates a hybrid pipeline method. Shows that simple keyword count heuristics are highly unreliable for academic sentiment analysis, and proves the efficacy of a low-cost LLM-assisted classification architecture in achieving near-zero error rates.
*   **For Future Developers**: Establishes a verified, structured SQLite database (`data/research.db`) and robust, open-source dashboard components for auditing future models.

---

### What Should Happen Next (Strategic Recommendations)
1.  **Implement Confidence Calibration UI**: LLMs must represent their certainty levels visually. Highly uncertain outputs should render in amber/yellow with automatic warnings, prompting the user to double-check.
2.  **Visible Version Control and Changelogs**: Platforms must provide absolute transparency. When model weights or safety parameters are modified, users should receive detailed changelogs to prevent silent trust breakdown.
3.  **Active Verification Integrations**: Product interfaces should embed "Fact-Check" buttons that run secondary web searches or check trusted academic database APIs automatically (similar to the user-created VerifyAI tool).
4.  **Extend Scoping**: Expand data ingestion to cover thread comments and developer forums (GitHub, Discord) to capture a broader spectrum of verification and debugging workflows.
