import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

db_path = Path("data/research.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = """
    SELECT p.id, p.score, p.title, p.selftext, a.evidence_quote, a.theme_rationale, a.model_confidence
    FROM post_analysis a
    JOIN posts p ON p.id = a.post_id
    WHERE a.primary_theme = 'real_world_impact_of_ai_outputs' AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
"""
rows = cur.execute(query).fetchall()

print(f"Total posts under real_world_impact_of_ai_outputs: {len(rows)}")

neg_words = ["ban", "banned", "fail", "fraud", "misconduct", "court", "lawyer", "attorney", "euthanize", "pharma", "clinical", "hospital", "police", "arrest", "charge", "cheating", "cheat", "scam", "billing", "billed", "security", "leak", "accident"]

candidates = []
for r in rows:
    title = (r["title"] or "").lower()
    text = (r["selftext"] or "").lower()
    quote = (r["evidence_quote"] or "").lower()
    rationale = (r["theme_rationale"] or "").lower()
    
    matches = []
    for w in neg_words:
        if w in title or w in quote or w in text:
            matches.append(w)
            
    if matches:
        candidates.append((len(matches), matches, r))

# Sort by number of matching negative words
candidates.sort(key=lambda x: x[0], reverse=True)

print("\nTOP NEGATIVE-CONSEQUENCE CANDIDATES UNDER THEME:")
for idx, (cnt, matches, r) in enumerate(candidates[:20]):
    print(f"\n#{idx+1}. ID: {r['id']} | Score: {r['score']} | Matches: {matches}")
    print(f"   Title: {r['title']}")
    print(f"   Quote: {r['evidence_quote']}")
    print(f"   Rationale: {r['theme_rationale']}")
    print("-" * 50)

conn.close()
