import sqlite3
import math
from pathlib import Path

THEME_KEYWORDS = {
    "persuasive_outputs_trust_formation": [
        "trust", "empathy", "comfort", "confident", "cautious", "caution", "expertise", "authority", 
        "persuasion", "persuasive", "language", "logic", "argument", "defend", "rationalization", 
        "convince", "expert", "sycophancy", "relationship", "certainty"
    ],
    "user_evaluation_verification_behavior": [
        "verify", "verification", "check", "fact-check", "audit", "checklist", "cite", "citation", 
        "source", "cross-check", "validation", "validate", "confirm", "double-check", "checking", "auditing",
        "papers", "quotes", "references", "citations", "accuracy", "factual"
    ],
    "real_world_impact_of_ai_outputs": [
        "consequence", "result", "impact", "legal", "attorney", "brief", "court", "fail", "failure", 
        "security", "attack", "exploit", "vulnerability", "financial", "money", "cost", "expense", 
        "grade", "exam", "homework", "cheat", "school", "academic", "decision", "harm", "damage", 
        "work", "job", "career", "doctor", "health", "medical", "prescription"
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

def calculate_score(row, theme_slug):
    title = (row["title"] or "").lower()
    text = (row["selftext"] or "").lower()
    quote = (row["evidence_quote"] or "").lower()
    rationale = (row["theme_rationale"] or "").lower()
    score = row["score"] or 0
    model_conf = row["model_confidence"]
    
    # 1. Classification Confidence
    conf_score = model_conf if model_conf is not None else 0.8
    
    # 2. Semantic Similarity
    keywords = THEME_KEYWORDS.get(theme_slug, [])
    similarity_score = 0.0
    for kw in keywords:
        if kw in quote or kw in title:
            similarity_score += 2.0
        elif kw in text or kw in rationale:
            similarity_score += 0.3
    similarity_score = min(similarity_score, 6.0)
    
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
    reddit_influence = 0.02 * math.log(score + 1)
    
    # 5. Penalties for meta-discussions, lists, comparisons, and fictional fanfics
    meta_indicators = ["list", "reasons", "manifesto", "comparison", "alternative", "asked chatgpt", "asked chat gpt", "what do you think", "versus", "vs", "fanfic", "write a", "fix seasons", "seasons 7", "how it would look", "future looks like", "rules.txt", "cheating", "ai partner", "fiction", "fictional", "story", "stories", "game of thrones"]
    penalty = 0.0
    for indicator in meta_indicators:
        if indicator in title or indicator in text[:200]:
            penalty += 2.5
            
    total_score = (conf_score * 2.0) + similarity_score + rationale_strength + reddit_influence - penalty
    return total_score

def main():
    db_path = Path("data/research.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    theme_slugs = [
        "overconfident_incorrect_outputs",
        "user_trust_breakdown",
        "over_reliance_on_ai_outputs",
        "user_evaluation_verification_behavior",
        "real_world_impact_of_ai_outputs",
        "persuasive_outputs_trust_formation"
    ]
    
    out_file = Path("scratch/simulate_ranking_output.txt")
    with out_file.open("w", encoding="utf-8") as f:
        for slug in theme_slugs:
            query = """
                SELECT p.id, p.title, p.selftext, p.score, p.url, a.evidence_quote, a.theme_rationale, a.model_confidence
                FROM post_analysis a
                JOIN posts p ON p.id = a.post_id
                WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
            """
            rows = cur.execute(query, (slug,)).fetchall()
            
            scored_rows = []
            for r in rows:
                score_val = calculate_score(r, slug)
                scored_rows.append((score_val, r))
                
            scored_rows.sort(key=lambda x: x[0], reverse=True)
            
            f.write(f"\n===== THEME: {slug} (Top 5 selected by algorithm) =====\n")
            for i, (score_val, r) in enumerate(scored_rows[:5]):
                f.write(f"  {i+1}. ID: {r['id']} | Alg Score: {score_val:.4f} | Reddit Score: {r['score']} | Conf: {r['model_confidence']}\n")
                f.write(f"     Title: {r['title']}\n")
                f.write(f"     Quote: {r['evidence_quote']}\n")
                f.write(f"     Rationale: {r['theme_rationale']}\n")
                f.write("\n")
                
    conn.close()
    print("Simulation results written to scratch/simulate_ranking_output.txt")

if __name__ == "__main__":
    main()
