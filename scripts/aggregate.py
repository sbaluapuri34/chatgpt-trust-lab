"""Phase 4: Aggregation script to compile database results into JSON/CSV insights."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from phase3.config import load_phase3_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def compute_deciles(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Assigns decile (1-10) to items based on 'score' in descending order."""
    sorted_items = sorted(items, key=lambda x: x["score"], reverse=True)
    n = len(sorted_items)
    if n == 0:
        return sorted_items

    for idx, item in enumerate(sorted_items):
        # 1-indexed decile, from 1 (highest scores) to 10 (lowest scores)
        decile = min(10, int(idx * 10 / n) + 1)
        item["decile"] = decile
    return sorted_items
# ----------------------------------------------------
# Qualitative Quote Ranking Keywords and Scoring Definitions
# ----------------------------------------------------
THEME_KEYWORDS = {
    "persuasive_outputs_trust_formation": [
        "why users trust", "confidence cues", "persuasive responses", "perceived expertise", 
        "authority signals", "trust formation", "trust", "empathy", "comfort", "confident", 
        "cautious", "caution", "expertise", "authority", "persuasion", "persuasive", "sycophancy", 
        "certainty", "trusting", "credibility", "logical", "logic", "fallacy", "fallacies", 
        "tactic", "tactics", "debate", "defend", "rhetoric", "rhetorical", "manipulation", 
        "sycophant", "relationship", "argument", "convince", "persuade"
    ],
    "user_evaluation_verification_behavior": [
        "fact checking", "source validation", "citation verification", "cross-checking", 
        "auditing chatgpt", "verify", "verification", "check", "fact-check", "audit", 
        "checklist", "cite", "citation", "source", "cross-check", "validation", "validate", 
        "confirm", "double-check", "checking", "auditing", "references", "papers", "quotes", 
        "citations", "accuracy", "factual", "verifyai", "google"
    ],
    "real_world_impact_of_ai_outputs": [
        "negative real-world consequences", "legal issues", "academic consequences", 
        "security failures", "financial consequences", "harmful decisions", "consequence", 
        "result", "impact", "legal", "attorney", "court", "custody", "lawyer", "fraud", 
        "euthanize", "euthanized", "saved life", "pharma", "medical", "doctor", "health", 
        "financial", "money", "billed", "cancel", "fee", "scam", "cheat", "homework", 
        "grade", "school", "academic", "harm", "damage", "consequences", "prompt injection", 
        "injection", "leak", "banned", "estate", "probate", "million", "audit", "cybertipline", 
        "reported", "therapist", "ban"
    ],
    "overconfident_incorrect_outputs": [
        "hallucination", "hallucinate", "incorrect", "wrong", "error", "mistake", "confidence", "overconfident", 
        "overconfidence", "fact", "fabricated", "false", "loop", "spiral", "untrustworthy"
    ],
    "user_trust_breakdown": [
        "breakdown", "erosion", "lose", "lost", "trust", "distrust", "disappointment", "scam", "scammed", 
        "cancel", "charge", "refund", "decline", "fail", "bad", "done", "frustrated"
    ],
    "over_reliance_on_ai_outputs": [
        "rely", "reliance", "over-reliance", "attach", "attachment", "companion", "companionship", 
        "friend", "therapy", "therapist", "psychologist", "addict", "addiction", "dependency"
    ]
}

ANALYTICAL_CONNECTORS = ["because", "demonstrates", "highlights", "shows", "illustrates", "indicates", "explains", "leads", "causes", "consequence", "impact", "reflects", "reveals", "exhibits", "documents"]

def calculate_representative_score(row: sqlite3.Row, theme_slug: str) -> float:
    """Calculates a mathematical representative score for qualitative posts."""
    import math
    title = (row["title"] or "").lower()
    text = (row["selftext"] or "").lower()
    quote = (row["evidence_quote"] or "").lower()
    rationale = (row["theme_rationale"] or "").lower()
    score = row["score"] or 0
    model_conf = row["model_confidence"]
    
    # 1. Classification Confidence
    conf_score = model_conf if model_conf is not None else 0.8
    
    # 2. Semantic Similarity with Split Caps
    keywords = THEME_KEYWORDS.get(theme_slug, [])
    title_quote_score = 0.0
    body_rationale_score = 0.0
    for kw in keywords:
        if kw in quote or kw in title:
            title_quote_score += 2.5
        elif kw in text or kw in rationale:
            body_rationale_score += 0.4
            
    similarity_score = min(title_quote_score, 5.0) + min(body_rationale_score, 1.5)
    
    # 3. Rationale Strength
    rationale_len = len(rationale)
    len_score = min(rationale_len / 150.0, 1.5)
    
    connector_score = 0.0
    for conn in ANALYTICAL_CONNECTORS:
        if conn in rationale:
            connector_score += 0.2
    connector_score = min(connector_score, 1.0)
    rationale_strength = len_score + connector_score
    
    # 4. Reduced Reddit Score influence (logarithmic minor tiebreaker)
    reddit_influence = 0.01 * math.log(score + 1)
    
    # 5. Penalties for meta-discussions, lists, comparisons, and fictional fanfics
    meta_indicators = [
        "list", "reasons", "manifesto", "comparison", "alternative", "asked chatgpt", "asked chat gpt", 
        "what do you think", "versus", "vs", "fanfic", "write a", "fix seasons", "seasons 7", 
        "how it would look", "future looks like", "rules.txt", "fiction", 
        "fictional", "story", "stories", "game of thrones", "prompt guide", "instructions for", "PSA:",
        "door closes", "neon-lit", "digital family", "romantic", "cheating", "exclusivity", "dating", 
        "ai partner", "love"
    ]
    penalty = 0.0
    for indicator in meta_indicators:
        if indicator in title or indicator in text[:200]:
            penalty += 3.0
            
    # Positive outcome penalties for Real-World Impact theme to highlight negative consequences
    if theme_slug == "real_world_impact_of_ai_outputs":
        positive_indicators = ["won custody", "full custody", "won full custody"]
        for pos_ind in positive_indicators:
            if pos_ind in title or pos_ind in quote or pos_ind in text[:100]:
                penalty += 4.0
            
    return (conf_score * 2.0) + similarity_score + rationale_strength + reddit_influence - penalty


def run_aggregation(cfg: Any, output_dir: Path) -> None:
    """Executes the aggregation process and writes outputs to the specified output_dir."""
    db_path = Path(cfg.db_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    theme_labels = {theme.slug: theme.label for theme in cfg.research_themes}
    theme_labels["mixed_or_multitheme"] = "Mixed / multi-theme"
    
    # ----------------------------------------------------
    # A. Research Theme Prevalence (theme_prevalence.csv)
    # ----------------------------------------------------
    logger.info("Computing theme prevalence...")
    q_prevalence = """
        SELECT a.primary_theme, COUNT(*) as raw_count, SUM(p.weight) as weighted_count
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme IS NOT NULL
        GROUP BY a.primary_theme
    """
    rows = cur.execute(q_prevalence).fetchall()
    
    total_raw = sum(r["raw_count"] for r in rows)
    total_weighted = sum(r["weighted_count"] for r in rows) if rows else 0.0
    
    prevalence_data = []
    for r in rows:
        slug = r["primary_theme"]
        label = theme_labels.get(slug, slug)
        raw_cnt = r["raw_count"]
        w_cnt = r["weighted_count"] or 0.0
        
        prevalence_data.append({
            "theme_slug": slug,
            "theme_label": label,
            "raw_count": raw_cnt,
            "raw_pct": round(raw_cnt / total_raw * 100, 2) if total_raw > 0 else 0.0,
            "weighted_count": round(w_cnt, 2),
            "weighted_pct": round(w_cnt / total_weighted * 100, 2) if total_weighted > 0.0 else 0.0
        })
        
    prevalence_path = output_dir / "theme_prevalence.csv"
    with prevalence_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["theme_slug", "theme_label", "raw_count", "raw_pct", "weighted_count", "weighted_pct"])
        writer.writeheader()
        writer.writerows(prevalence_data)
    logger.info("Saved theme prevalence to %s", prevalence_path)
    
    # ----------------------------------------------------
    # B. Secondary Themes Co-occurrence Matrix (theme_cooccurrence.json)
    # ----------------------------------------------------
    logger.info("Computing theme co-occurrence...")
    q_cooccurrence = """
        SELECT primary_theme, secondary_themes
        FROM post_analysis
        WHERE primary_theme IS NOT NULL
    """
    rows_co = cur.execute(q_cooccurrence).fetchall()
    
    matrix: dict[str, dict[str, int]] = {}
    all_slugs = list(theme_labels.keys())
    for s1 in all_slugs:
        matrix[s1] = {s2: 0 for s2 in all_slugs}
        
    for r in rows_co:
        p_theme = r["primary_theme"]
        if p_theme not in matrix:
            continue
        try:
            s_themes = json.loads(r["secondary_themes"] or "[]")
        except Exception:
            s_themes = []
            
        for s_theme in s_themes:
            s_theme = str(s_theme).strip()
            if s_theme in matrix[p_theme]:
                matrix[p_theme][s_theme] += 1
                
    cooccurrence_path = output_dir / "theme_cooccurrence.json"
    with cooccurrence_path.open("w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)
    logger.info("Saved theme co-occurrence to %s", cooccurrence_path)
    
    # ----------------------------------------------------
    # C. Trust Erosion Diagnostic Panel (trust_erosion_report.json)
    # ----------------------------------------------------
    logger.info("Computing trust erosion diagnostic...")
    q_trust = """
        SELECT a.primary_theme, f.match_trust_loss
        FROM post_analysis a
        JOIN post_features f ON f.post_id = a.post_id
        WHERE a.primary_theme IS NOT NULL
    """
    rows_t = cur.execute(q_trust).fetchall()
    
    tp = 0  # True Positive: Labeled trust_erosion, has match_trust_loss >= 1
    fp = 0  # False Positive: Labeled trust_erosion, has match_trust_loss == 0
    fn = 0  # False Negative: Labeled other theme, has match_trust_loss >= 1
    tn = 0  # True Negative: Labeled other theme, has match_trust_loss == 0
    
    for r in rows_t:
        is_labeled_erosion = (r["primary_theme"] == "user_trust_breakdown")
        has_signal = (r["match_trust_loss"] >= 1)
        
        if is_labeled_erosion and has_signal:
            tp += 1
        elif is_labeled_erosion and not has_signal:
            fp += 1
        elif not is_labeled_erosion and has_signal:
            fn += 1
        else:
            tn += 1
            
    total_samples = len(rows_t)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    trust_report = {
        "metrics": {
            "total_relevant_posts": total_samples,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "precision_of_signal": round(precision, 4),
            "recall_of_signal": round(recall, 4),
            "f1_score": round(f1, 4)
        },
        "interpretation": (
            "This diagnostic panel compares the final LLM-assigned 'trust_erosion' research theme with "
            "the preprocessing keyword pre-screening signal 'match_trust_loss'. A high precision "
            "indicates that keyword matches are highly predictive of final thematic alignment, while "
            "recall measures how many trust erosion posts had pre-screening flags."
        )
    }
    
    trust_path = output_dir / "trust_erosion_report.json"
    with trust_path.open("w", encoding="utf-8") as f:
        json.dump(trust_report, f, indent=2, ensure_ascii=False)
    logger.info("Saved trust erosion report to %s", trust_path)
    
    # ----------------------------------------------------
    # D. Severity Distributions (severity_distribution.csv)
    # ----------------------------------------------------
    logger.info("Computing severity distributions...")
    q_severity = """
        SELECT a.primary_theme, a.severity, COUNT(*) as raw_count, SUM(p.weight) as weighted_count
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme IS NOT NULL AND a.severity IS NOT NULL
        GROUP BY a.primary_theme, a.severity
    """
    rows_sev = cur.execute(q_severity).fetchall()
    
    severity_data = []
    for r in rows_sev:
        slug = r["primary_theme"]
        label = theme_labels.get(slug, slug)
        raw_cnt = r["raw_count"]
        w_cnt = r["weighted_count"] or 0.0
        
        severity_data.append({
            "theme_slug": slug,
            "theme_label": label,
            "severity": r["severity"],
            "raw_count": raw_cnt,
            "weighted_count": round(w_cnt, 2)
        })
        
    severity_path = output_dir / "severity_distribution.csv"
    with severity_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["theme_slug", "theme_label", "severity", "raw_count", "weighted_count"])
        writer.writeheader()
        writer.writerows(severity_data)
    logger.info("Saved severity distribution to %s", severity_path)
    
    # ----------------------------------------------------
    # E. Score Decile Impact Analysis (score_impact.csv)
    # ----------------------------------------------------
    logger.info("Computing score decile impact...")
    q_scores = """
        SELECT p.score, a.primary_theme
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme IS NOT NULL
    """
    rows_s = [dict(r) for r in cur.execute(q_scores).fetchall()]
    binned = compute_deciles(rows_s)
    
    # Count of themes per decile
    decile_counts: dict[int, dict[str, int]] = {d: {slug: 0 for slug in theme_labels} for d in range(1, 11)}
    decile_totals: dict[int, int] = {d: 0 for d in range(1, 11)}
    
    for item in binned:
        d = item["decile"]
        slug = item["primary_theme"]
        if slug in decile_counts[d]:
            decile_counts[d][slug] += 1
            decile_totals[d] += 1
            
    score_data = []
    for d in range(1, 11):
        tot = decile_totals[d]
        for slug in theme_labels:
            cnt = decile_counts[d][slug]
            label = theme_labels[slug]
            score_data.append({
                "decile": d,
                "theme_slug": slug,
                "theme_label": label,
                "raw_count": cnt,
                "decile_prevalence_pct": round(cnt / tot * 100, 2) if tot > 0 else 0.0
            })
            
    score_path = output_dir / "score_impact.csv"
    with score_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["decile", "theme_slug", "theme_label", "raw_count", "decile_prevalence_pct"])
        writer.writeheader()
        writer.writerows(score_data)
    logger.info("Saved score decile impact to %s", score_path)
    
    # ----------------------------------------------------
    # F. Top Representative Evidence Quotes (representative_quotes.json)
    # ----------------------------------------------------
    logger.info("Extracting representative evidence quotes...")
    quotes_data: dict[str, list[dict[str, Any]]] = {}
    
    for slug in theme_labels:
        quotes_data[slug] = []
        # Query all posts matching the primary theme which have a valid quote
        q_all_quotes = """
            SELECT p.title, p.selftext, p.score, p.weight, p.url, a.evidence_quote, a.theme_rationale, a.model_confidence
            FROM post_analysis a
            JOIN posts p ON p.id = a.post_id
            WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
        """
        rows = cur.execute(q_all_quotes, (slug,)).fetchall()
        
        # Calculate mathematical score for each quote
        scored_rows = []
        for r in rows:
            rep_score = calculate_representative_score(r, slug)
            scored_rows.append((rep_score, r))
            
        # Sort descending by representative score
        scored_rows.sort(key=lambda x: x[0], reverse=True)
        
        # Select top 5
        for score_val, r in scored_rows[:5]:
            quotes_data[slug].append({
                "score": r["score"],
                "weight": round(r["weight"], 4),
                "url": r["url"],
                "evidence_quote": r["evidence_quote"],
                "theme_rationale": r["theme_rationale"]
            })
            
    quotes_path = output_dir / "representative_quotes.json"
    with quotes_path.open("w", encoding="utf-8") as f:
        json.dump(quotes_data, f, indent=2, ensure_ascii=False)
    logger.info("Saved representative quotes to %s", quotes_path)
    
    # ----------------------------------------------------
    # G. Platform Methodology & Cost Funnel snippet (methodology_snippet.json)
    # ----------------------------------------------------
    logger.info("Generating methodology snippet...")
    total_raw_ingested = cur.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    total_candidates = cur.execute("SELECT COUNT(*) FROM post_features WHERE is_candidate = 1").fetchone()[0]
    total_relevant = cur.execute("SELECT COUNT(*) FROM post_analysis WHERE stage1_relevant = 1").fetchone()[0]
    total_analyzed = cur.execute("SELECT COUNT(*) FROM post_analysis WHERE primary_theme IS NOT NULL").fetchone()[0]
    
    funnel = {
        "funnel_table": {
            "total_ingested_raw_posts": total_raw_ingested,
            "preselected_keyword_candidates": total_candidates,
            "stage1_confirmed_relevant_posts": total_relevant,
            "stage2_deep_theme_analyzed_posts": total_analyzed
        },
        "methodology_disclaimer": (
            "DISTINCTION SNIPPET: Phase 2 preprocessing keyword match metrics (Confidence, Hallucinations, "
            "Trust, consequences) are statistical markers used solely for pre-screening candidates. "
            "They represent simple substring counts. In contrast, Phase 3 Research Themes (assigned by "
            "Groq llama-3.1-8b-instant) represent semantic, human-aligned categorizations based on full post "
            "narratives. Final analysis dashboard and charts MUST use Stage 2 primary/secondary themes only."
        )
    }
    
    funnel_path = output_dir / "methodology_snippet.json"
    with funnel_path.open("w", encoding="utf-8") as f:
        json.dump(funnel, f, indent=2, ensure_ascii=False)
    logger.info("Saved methodology snippet to %s", funnel_path)
    
    # ----------------------------------------------------
    # H. Monthly Theme Trends (monthly_theme_trends.csv)
    # ----------------------------------------------------
    logger.info("Computing monthly theme trends...")
    q_monthly = """
        SELECT strftime('%Y-%m', datetime(p.created_utc, 'unixepoch')) as month,
               a.primary_theme,
               COUNT(*) as raw_count,
               SUM(p.weight) as weighted_count
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme IS NOT NULL
        GROUP BY month, a.primary_theme
    """
    rows_m = cur.execute(q_monthly).fetchall()
    
    monthly_totals = {}
    for r in rows_m:
        month = r["month"]
        raw_cnt = r["raw_count"]
        w_cnt = r["weighted_count"] or 0.0
        
        if month not in monthly_totals:
            monthly_totals[month] = {"raw_total": 0, "weighted_total": 0.0}
        
        monthly_totals[month]["raw_total"] += raw_cnt
        monthly_totals[month]["weighted_total"] += w_cnt
        
    monthly_data = []
    for r in rows_m:
        month = r["month"]
        slug = r["primary_theme"]
        label = theme_labels.get(slug, slug)
        raw_cnt = r["raw_count"]
        w_cnt = r["weighted_count"] or 0.0
        
        totals = monthly_totals[month]
        raw_pct = round(raw_cnt / totals["raw_total"] * 100, 2) if totals["raw_total"] > 0 else 0.0
        weighted_pct = round(w_cnt / totals["weighted_total"] * 100, 2) if totals["weighted_total"] > 0.0 else 0.0
        
        monthly_data.append({
            "month": month,
            "theme_slug": slug,
            "theme_label": label,
            "raw_count": raw_cnt,
            "weighted_count": round(w_cnt, 2),
            "raw_percentage": raw_pct,
            "weighted_percentage": weighted_pct
        })
        
    monthly_data = sorted(monthly_data, key=lambda x: (x["month"], -x["raw_count"]))
    
    monthly_trends_path = output_dir / "monthly_theme_trends.csv"
    with monthly_trends_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["month", "theme_slug", "theme_label", "raw_count", "weighted_count", "raw_percentage", "weighted_percentage"])
        writer.writeheader()
        writer.writerows(monthly_data)
    logger.info("Saved monthly theme trends to %s", monthly_trends_path)
    
    conn.close()


def main() -> int:
    logger.info("Starting Phase 4 Aggregation...")
    try:
        cfg = load_phase3_config()
        output_dir = Path("data/aggregated")
        run_aggregation(cfg, output_dir)
        logger.info("Phase 4 Aggregation completed successfully!")
        return 0
    except Exception as e:
        logger.error("Aggregation failed: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
