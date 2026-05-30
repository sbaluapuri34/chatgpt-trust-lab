import sqlite3
import math
import json
from pathlib import Path

# Definitions of target keywords for each theme
THEME_KEYWORDS = {
    "persuasive_outputs_trust_formation": {
        "priority": ["trust", "empathy", "comfort", "confident", "cautious", "caution", "expertise", "authority", "persuasion", "persuasive", "language", "logic", "argument", "defend", "rationalization", "convince", "expert", "sycophancy", "relationship", "certainty"],
        "definition": "posts discussing why users trust ChatGPT, persuasive language, confidence cues, perceived expertise, authority signals, trust formation."
    },
    "user_evaluation_verification_behavior": {
        "priority": ["verify", "verification", "check", "fact-check", "audit", "checklist", "cite", "citation", "source", "cross-check", "validation", "validate", "confirm", "double-check", "checking", "auditing"],
        "definition": "posts discussing fact checking, source validation, citation verification, cross-checking, auditing ChatGPT outputs."
    },
    "real_world_impact_of_ai_outputs": {
        "priority": ["consequence", "result", "impact", "legal", "attorney", "brief", "court", "fail", "failure", "security", "attack", "exploit", "vulnerability", "financial", "money", "cost", "expense", "grade", "exam", "homework", "cheat", "school", "academic", "decision", "harm", "damage", "cheat", "work", "job", "career", "doctor", "health", "medical", "prescription"],
        "definition": "posts discussing negative real-world consequences, legal issues, academic consequences, security failures, financial consequences, harmful decisions influenced by ChatGPT."
    }
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
    keywords = THEME_KEYWORDS[theme_slug]["priority"]
    similarity_score = 0.0
    matched_keywords = []
    for kw in keywords:
        kw_found = False
        # Keyword in quote or title gets higher weight
        if kw in quote or kw in title:
            similarity_score += 1.0
            kw_found = True
        elif kw in text or kw in rationale:
            similarity_score += 0.5
            kw_found = True
        if kw_found:
            matched_keywords.append(kw)
    # Cap similarity score at 6.0
    similarity_score = min(similarity_score, 6.0)
    
    # 3. Rationale Strength
    rationale_len = len(rationale)
    # Give up to 1.5 points for length (optimal length >= 150 chars)
    len_score = min(rationale_len / 150.0, 1.5)
    
    # Analytical connectors check
    connector_score = 0.0
    for conn in ANALYTICAL_CONNECTORS:
        if conn in rationale:
            connector_score += 0.2
    connector_score = min(connector_score, 1.0)
    rationale_strength = len_score + connector_score
    
    # 4. Dampened Reddit Score (Tiebreaker)
    # Max score ~ 30,000, log(30000+1) ~ 10.3. Multiplier of 0.02 yields max 0.2 points.
    reddit_influence = 0.02 * math.log(score + 1)
    
    total_score = (conf_score * 2.0) + similarity_score + rationale_strength + reddit_influence
    
    return {
        "total_score": round(total_score, 4),
        "conf_score": round(conf_score, 2),
        "similarity_score": round(similarity_score, 2),
        "rationale_strength": round(rationale_strength, 2),
        "reddit_influence": round(reddit_influence, 4),
        "matched_keywords": matched_keywords
    }

def main():
    db_path = Path("data/research.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    target_themes = list(THEME_KEYWORDS.keys())
    
    rankings_output = []
    
    for theme in target_themes:
        query = """
            SELECT p.id, p.title, p.selftext, p.score, p.url, a.evidence_quote, a.theme_rationale, a.model_confidence
            FROM post_analysis a
            JOIN posts p ON p.id = a.post_id
            WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
        """
        rows = cur.execute(query, (theme,)).fetchall()
        
        scored_posts = []
        for r in rows:
            details = calculate_score(r, theme)
            scored_posts.append({
                "id": r["id"],
                "title": r["title"],
                "score": r["score"],
                "url": r["url"],
                "evidence_quote": r["evidence_quote"],
                "theme_rationale": r["theme_rationale"],
                "metrics": details
            })
            
        # Sort by total_score descending
        scored_posts.sort(key=lambda x: x["metrics"]["total_score"], reverse=True)
        
        rankings_output.append({
            "theme": theme,
            "posts": scored_posts
        })
        
    # Write details to file for audit
    with open("scratch/rankings_audit.txt", "w", encoding="utf-8") as f:
        for item in rankings_output:
            theme = item["theme"]
            f.write(f"=== THEME: {theme} ===\n")
            f.write(f"Definition focus: {THEME_KEYWORDS[theme]['definition']}\n\n")
            for idx, p in enumerate(item["posts"][:15]):
                f.write(f"Rank {idx+1} | Score: {p['metrics']['total_score']} | Post ID: {p['id']} | Reddit Score: {p['score']}\n")
                f.write(f"Title: {p['title']}\n")
                f.write(f"Quote: {p['evidence_quote']}\n")
                f.write(f"Rationale: {p['theme_rationale']}\n")
                f.write(f"Metrics: Conf={p['metrics']['conf_score']}, Sim={p['metrics']['similarity_score']}, RatStr={p['metrics']['rationale_strength']}, Reddit={p['metrics']['reddit_influence']}\n")
                f.write(f"Keywords matched: {p['metrics']['matched_keywords']}\n")
                f.write("-" * 80 + "\n")
            f.write("\n" + "="*80 + "\n\n")
            
    conn.close()
    print("Rankings compiled in scratch/rankings_audit.txt")

if __name__ == "__main__":
    main()
