import sys
sys.path.append(r"c:\Users\user\REDDIT ANALYSER")

import sqlite3
import math
from scripts.aggregate import THEME_KEYWORDS, ANALYTICAL_CONNECTORS

def check_score(row, theme_slug):
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
    
    print("Keywords found in title/quote:")
    for kw in keywords:
        if kw in quote or kw in title:
            print(f"  - '{kw}' in title or quote (+2.5)")
            title_quote_score += 2.5
        elif kw in text or kw in rationale:
            print(f"  - '{kw}' in body or rationale (+0.4)")
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
    
    print(f"Components:")
    print(f"  Confidence component: {conf_score * 2.0:.4f}")
    print(f"  Similarity component: {similarity_score:.4f} (title_quote_score: {title_quote_score}, body_rationale_score: {body_rationale_score})")
    print(f"  Rationale strength: {rationale_strength:.4f} (len_score: {len_score:.4f}, connector_score: {connector_score:.4f})")
    print(f"  Reddit influence: {reddit_influence:.4f}")
    
    return (conf_score * 2.0) + similarity_score + rationale_strength + reddit_influence

conn = sqlite3.connect("data/research.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

row = cur.execute("SELECT p.title, p.selftext, p.score, a.evidence_quote, a.theme_rationale, a.model_confidence FROM post_analysis a JOIN posts p ON p.id = a.post_id WHERE p.id = '1n786hp'").fetchone()

if row:
    print(f"ID: 1n786hp")
    print(f"Title: {row['title']}")
    print(f"Quote: {row['evidence_quote']}")
    print(f"Rationale: {row['theme_rationale']}")
    score_val = check_score(row, "real_world_impact_of_ai_outputs")
    print(f"Total Score: {score_val:.4f}")
else:
    print("Post 1n786hp not found!")
conn.close()
