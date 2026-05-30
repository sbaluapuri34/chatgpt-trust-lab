import sqlite3

conn = sqlite3.connect("data/research.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = """
    SELECT p.id, p.title, p.score, p.weight, p.url, a.evidence_quote, a.theme_rationale, a.model_confidence
    FROM post_analysis a
    JOIN posts p ON p.id = a.post_id
    WHERE a.primary_theme = 'real_world_impact_of_ai_outputs'
"""
rows = cur.execute(query).fetchall()

with open("scratch/real_world_posts.txt", "w", encoding="utf-8") as f:
    f.write(f"Total posts: {len(rows)}\n\n")
    for r in rows:
        f.write("="*80 + "\n")
        f.write(f"ID: {r['id']} | Score: {r['score']} | Conf: {r['model_confidence']}\n")
        f.write(f"Title: {r['title']}\n")
        f.write(f"URL: {r['url']}\n")
        f.write(f"Quote: {r['evidence_quote']}\n")
        f.write(f"Rationale: {r['theme_rationale']}\n")

print("Successfully wrote real_world_posts.txt")
conn.close()
