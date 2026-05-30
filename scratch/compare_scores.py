import sys
sys.path.append(r"c:\Users\user\REDDIT ANALYSER")

import sqlite3
import math

from scripts.aggregate import THEME_KEYWORDS, ANALYTICAL_CONNECTORS

def calculate_score_no_penalty(row, theme_slug):
    title = (row["title"] or "").lower()
    text = (row["selftext"] or "").lower()
    quote = (row["evidence_quote"] or "").lower()
    rationale = (row["theme_rationale"] or "").lower()
    score = row["score"] or 0
    model_conf = row["model_confidence"]
    
    conf_score = model_conf if model_conf is not None else 0.8
    
    keywords = THEME_KEYWORDS.get(theme_slug, [])
    title_quote_score = 0.0
    body_rationale_score = 0.0
    for kw in keywords:
        if kw in quote or kw in title:
            title_quote_score += 2.5
        elif kw in text or kw in rationale:
            body_rationale_score += 0.4
            
    similarity_score = min(title_quote_score, 5.0) + min(body_rationale_score, 1.5)
    
    rationale_len = len(rationale)
    len_score = min(rationale_len / 150.0, 1.5)
    
    connector_score = 0.0
    for conn in ANALYTICAL_CONNECTORS:
        if conn in rationale:
            connector_score += 0.2
    connector_score = min(connector_score, 1.0)
    rationale_strength = len_score + connector_score
    
    reddit_influence = 0.01 * math.log(score + 1)
    
    # Base penalty only (no positive outcome penalty)
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
            
    return (conf_score * 2.0) + similarity_score + rationale_strength + reddit_influence - penalty

conn = sqlite3.connect("data/research.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

ids = ["1nm928n", "1sc6zf0", "1oons00", "1nkbyln", "1ovafq9", "1n786hp", "1pw2ciz", "1rjxeb0"]

query = """
    SELECT p.id, p.title, p.selftext, p.score, p.weight, p.url, a.evidence_quote, a.theme_rationale, a.model_confidence
    FROM post_analysis a
    JOIN posts p ON p.id = a.post_id
    WHERE p.id IN ({})
""".format(",".join(["?"] * len(ids)))

rows = cur.execute(query, ids).fetchall()
scored = []
for r in rows:
    score_val = calculate_score_no_penalty(r, "real_world_impact_of_ai_outputs")
    scored.append((score_val, r))
    
scored.sort(key=lambda x: x[0], reverse=True)

print("Scored target posts (no positive outcome penalty):")
for val, r in scored:
    print(f"ID: {r['id']} | Score: {val:.4f} | Title: {r['title'][:80]}")

conn.close()
