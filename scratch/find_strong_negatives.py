import sys
sys.path.append(r"c:\Users\user\REDDIT ANALYSER")

import sqlite3
import math
from scripts.aggregate import calculate_representative_score

conn = sqlite3.connect("data/research.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = """
    SELECT p.id, p.title, p.selftext, p.score, p.weight, p.url, a.evidence_quote, a.theme_rationale, a.model_confidence
    FROM post_analysis a
    JOIN posts p ON p.id = a.post_id
    WHERE a.primary_theme = 'real_world_impact_of_ai_outputs' AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
"""
rows = cur.execute(query).fetchall()

negatives = []
for r in rows:
    title = (r["title"] or "").lower()
    text = (r["selftext"] or "").lower()
    quote = (r["evidence_quote"] or "").lower()
    rationale = (r["theme_rationale"] or "").lower()
    
    # Check if this post describes a negative outcome (legal, financial, security, health, academic consequences)
    is_positive = any(word in title or word in quote for word in ["won custody", "full custody", "won full custody", "saved my life", "prevented euthanasia"])
    
    if not is_positive:
        score_val = calculate_representative_score(r, "real_world_impact_of_ai_outputs")
        negatives.append((score_val, r))

negatives.sort(key=lambda x: x[0], reverse=True)

print("Top 10 Negative Consequence Examples under Real-World Impact:")
for idx, (val, r) in enumerate(negatives[:10]):
    print(f"\n{idx+1}. ID: {r['id']} | Score: {val:.4f} | Upvotes: {r['score']}")
    print(f"   Title: {r['title']}")
    print(f"   Quote: {r['evidence_quote']}")
    print(f"   Rationale: {r['theme_rationale']}")

conn.close()
