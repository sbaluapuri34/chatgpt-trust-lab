# Calculation Appendix
**ChatGPT Output Trust & Evaluation Lab (ChatGPT Trust Lab)**
*Rigorous Mathematical Formulas, Inputs, Data Sources, and Metric Interpretations*

---

## 1. Engagement Weighting Heuristic

### Mathematical Formula
For any given post $i$, the **Engagement Weight** ($W_i$) is calculated using a log-scaled upvote heuristic to manage extreme outliers in upvote distributions:
$$W_i = \ln(1 + \max(\text{score}_i, 0))$$

### Inputs
*   `score_i`: The raw upvote score of Reddit post $i$. If a post has a negative score, it is capped at `0` using the `max` function to prevent complex numbers or negative weights.

### Data Source
*   `posts` table in `data/research.db` (specifically the `score` column).

### Interpretation
*   **Purpose**: Traditional averages are highly distorted by single viral posts that receive 10,000+ upvotes. The natural logarithm ($\ln$) compresses these values, ensuring that a post with 10,000 upvotes is given higher importance than a post with 1 upvote, but does not completely drown out hundreds of other valid user experiences.
*   **Result Scale**: A post with a score of `0` has a weight of $W_0 = \ln(1) = 0.0$. A post with a score of `100` has a weight of $W_{100} = \ln(101) \approx 4.61$. A highly viral post with a score of `12,526` has a weight of $W_{12526} = \ln(12527) \approx 9.44$.

---

## 2. Theme Prevalence Calculations

The dashboard presents two different prevalence metrics to map the distribution of the 6 core research themes across the 594 confirmed relevant posts.

### 1. Raw Theme Prevalence
#### Formula
For a given theme $T$:
$$P_{T,\text{raw}} = \frac{N_T}{N_{\text{total}}} \times 100\%$$
Where:
*   $N_T$: The number of posts where the primary theme is classified as $T$.
*   $N_{\text{total}}$: The total number of confirmed relevant posts ($N_{\text{total}} = 594$).

#### Inputs
*   `primary_theme` count from `post_analysis` where `stage1_relevant = 1`.

#### Interpretation
*   Measures the simple frequency of occurrence. It answers: *"What percentage of documented user stories align primarily to this theme, regardless of how much attention they received?"*

### 2. Weighted Theme Prevalence
#### Formula
For a given theme $T$:
$$P_{T,\text{weighted}} = \frac{\sum_{i \in T} W_i}{\sum_{j = 1}^{N_{\text{total}}} W_j} \times 100\%$$
Where:
*   $W_i$: The engagement weight of post $i$ belonging to theme $T$.
*   $W_j$: The engagement weight of post $j$ in the entire relevant corpus.

#### Inputs
*   Post `score` and `primary_theme` matching from `data/research.db`.

#### Interpretation
*   Measures the community-validated attention share. It answers: *"What percentage of active community engagement and viral discussion is driven by this theme?"* A spike in weighted prevalence indicates a theme containing highly resonant, viral community stories.

---

## 3. Severity Distribution

### Formula
For a given theme $T$ and severity level $S \in \{\text{low}, \text{medium}, \text{high}\}$:
$$D_{T,S} = \frac{N_{T,S}}{N_T} \times 100\%$$
Where:
*   $N_{T,S}$: The number of posts within theme $T$ classified under severity level $S$.
*   $N_T$: The total number of posts classified under theme $T$.

### Inputs
*   `severity` column and `primary_theme` column from the `post_analysis` table.

### Interpretation
*   Indicates the risk profile of each research theme. 
    *   **High Severity**: Represents posts detailing severe downstream consequences (e.g. professional damage, financial loss, near-fatal pet errors).
    *   **Medium Severity**: Represents significant disruptions, user confusion, or moderate trust erosion (e.g., spending hours debugging a hallucinated package).
    *   **Low Severity**: Represents minor errors, general annoyances, or conversational comments showing no direct downstream damage.

---

## 4. Co-occurrence Matrix Counts

### Formula
For primary theme $A$ and secondary theme $B$:
$$C_{A,B} = \sum_{i = 1}^{N_{\text{total}}} \mathbb{I}(T_{p,i} = A \land B \in T_{s,i})$$
Where:
*   $\mathbb{I}(\cdot)$ is the indicator function (returns `1` if true, `0` if false).
*   $T_{p,i}$: The primary theme of post $i$.
*   $T_{s,i}$: The array of secondary themes assigned to post $i$.

### Inputs
*   `primary_theme` and `secondary_themes` (parsed from JSON strings) in `post_analysis` table.

### Interpretation
*   Identifies cross-theme intersections. If a post has a primary theme of `confidently_incorrect_outputs` but also contains `real_world_impact_of_ai_outputs` as a secondary theme, it increment the co-occurrence count. This reveals which model failures are the direct drivers of downstream consequences.

---

## 5. Diagnostic Accuracy Metrics (Keyword vs. LLM)

These calculations compare the deterministic keyword flag `match_trust_loss` in Phase 2 (Preprocessing) with the final semantic `user_trust_breakdown` primary theme in Phase 3 (LLM Analysis).

```
                             Confirmed Semantic Theme (LLM)
                             User Trust Breakdown     Other Theme
                        ┌─────────────────────────┬────────────────────────┐
   Phase 2 Keyword      │   True Positive (TP)    │  False Positive (FP)   │
   Flag: match_trust    │         TP = 36         │        FP = 288        │
                        ├─────────────────────────┼────────────────────────┤
   Phase 2 Keyword      │  False Negative (FN)    │   True Negative (TN)   │
   Flag: NO match       │         FN = 54         │        TN = 216        │
                        └─────────────────────────┴────────────────"──────┘
```

### 1. Precision (Precision of Signal)
#### Formula
$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{36}{36 + 288} = \frac{36}{324} \approx 11.11\%$$

#### Inputs
*   `TP` (True Positives): Posts flagged with keyword `trust_loss` and labeled as `user_trust_breakdown` by the LLM.
*   `FP` (False Positives): Posts flagged with keyword `trust_loss` but classified as a different theme by the LLM.

#### Interpretation
*   **Meaning**: Measures the purity of the keyword signal. Out of all threads containing the word "trust", only 11.11% actually describe an authentic breakdown of user trust. The remaining 88.89% represent noise (negated expressions, meta-discussions, or out-of-context phrases).

### 2. Recall (Recall of Signal)
#### Formula
$$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{36}{36 + 54} = \frac{36}{90} \approx 40.00\%$$

#### Inputs
*   `FN` (False Negatives): Posts **not** flagged with keyword `trust_loss` but classified as `user_trust_breakdown` by the LLM.

#### Interpretation
*   **Meaning**: Measures the capture rate of the keyword filter. Out of all posts that are semantically determined to represent a breakdown in user trust, only 40.0% are captured by the literal search term "trust". The remaining 60.0% express trust erosion **implicitly** (using synonyms or describing negative feelings/consequences without using the literal word "trust").

### 3. F1-Score
#### Formula
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = 2 \times \frac{0.1111 \times 0.40}{0.1111 + 0.40} \approx 0.1739$$

#### Interpretation
*   The harmonic mean of precision and recall. A low F1-score (0.17) mathematically proves the severe limitations of deterministic keyword pre-screening and validates the transition to semantic LLM evaluation.

---

## 6. Methodology Funnel Calculations

The sidebar methodology funnel calculates conversion rates across the four pipeline stages to track data volume and retention.

### 1. Preselected Keyword Candidate Rate
$$\text{Candidate Rate} = \frac{N_{\text{candidates}}}{N_{\text{raw}}} \times 100\% = \frac{729}{1,091} \times 100\% \approx 66.82\%$$

### 2. Stage 1 Confirmed Relevance Rate
$$\text{Relevance Rate} = \frac{N_{\text{relevant}}}{N_{\text{candidates}}} \times 100\% = \frac{594}{729} \times 100\% \approx 81.48\%$$

### 3. Overall Pipeline Conversion Rate
$$\text{Pipeline Conversion} = \frac{N_{\text{relevant}}}{N_{\text{raw}}} \times 100\% = \frac{594}{1,091} \times 100\% \approx 54.45\%$$
