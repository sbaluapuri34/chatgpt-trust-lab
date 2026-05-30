import sqlite3
from pathlib import Path

db_path = Path("data/research.db")
if not db_path.exists():
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

themes = [
    "persuasive_outputs_trust_formation",
    "user_evaluation_verification_behavior",
    "real_world_impact_of_ai_outputs"
]

with open("scratch/db_dump.txt", "w", encoding="utf-8") as f:
    for theme in themes:
        f.write("=" * 80 + "\n")
        f.write(f"THEME: {theme}\n")
        f.write("=" * 80 + "\n")
        
        query = """
            SELECT p.id, p.score, p.title, p.selftext, a.evidence_quote, a.theme_rationale, a.model_confidence
            FROM post_analysis a
            JOIN posts p ON p.id = a.post_id
            WHERE a.primary_theme = ?
        """
        rows = cur.execute(query, (theme,)).fetchall()
        f.write(f"Found {len(rows)} posts under {theme}:\n")
        
        # Sort by score descending to see what the top ones are
        sorted_rows = sorted(rows, key=lambda x: x["score"] or 0, reverse=True)
        
        for idx, r in enumerate(sorted_rows):
            f.write(f"\n--- Post #{idx+1} | ID: {r['id']} | Score: {r['score']} | Confidence: {r['model_confidence']} ---\n")
            f.write(f"Title: {r['title']}\n")
            f.write(f"Evidence Quote: {r['evidence_quote']}\n")
            f.write(f"Rationale: {r['theme_rationale']}\n")
            body = r['selftext'] or ""
            if len(body) > 300:
                f.write(f"Body (truncated): {body[:300]}...\n")
            else:
                f.write(f"Body: {body}\n")

conn.close()
print("Dumping finished successfully!")
