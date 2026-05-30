import sys
sys.path.append(r"c:\Users\user\REDDIT ANALYSER")

import sqlite3
import math

from scripts.aggregate import calculate_representative_score

conn = sqlite3.connect("data/research.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

themes = [
    "persuasive_outputs_trust_formation",
    "user_evaluation_verification_behavior",
    "real_world_impact_of_ai_outputs"
]

for theme in themes:
    print(f"\n==================== THEME: {theme} ====================")
    query = """
        SELECT p.id, p.title, p.selftext, p.score, p.weight, p.url, a.evidence_quote, a.theme_rationale, a.model_confidence
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
    """
    rows = cur.execute(query, (theme,)).fetchall()
    
    scored = []
    for r in rows:
        score_val = calculate_representative_score(r, theme)
        scored.append((score_val, r))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    
    print(f"Top 10 scored posts:")
    for idx, (val, r) in enumerate(scored[:10]):
        print(f"{idx+1}. ID: {r['id']} | Score: {val:.4f} | Upvotes: {r['score']} | Conf: {r['model_confidence']}")
        print(f"   Title: {r['title']}")
        print(f"   Quote: {r['evidence_quote'][:120]}...")
        print(f"   Rationale: {r['theme_rationale'][:120]}...")

conn.close()
