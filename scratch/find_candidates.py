import sqlite3
import json

conn = sqlite3.connect('data/research.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def dump_theme(theme_slug, filename):
    query = """
        SELECT p.id, p.score, p.title, p.selftext, a.evidence_quote, a.theme_rationale
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
        ORDER BY p.score DESC
    """
    rows = cur.execute(query, (theme_slug,)).fetchall()
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"=== {theme_slug} ===\n\n")
        for idx, r in enumerate(rows):
            f.write(f"Index: {idx+1}\n")
            f.write(f"ID: {r['id']}\n")
            f.write(f"Score: {r['score']}\n")
            f.write(f"Title: {r['title']}\n")
            f.write(f"Quote: {r['evidence_quote']}\n")
            f.write(f"Rationale: {r['theme_rationale']}\n")
            f.write(f"Excerpt: {(r['selftext'] or '')[:300].replace('\n', ' ')}\n")
            f.write("-" * 80 + "\n")

dump_theme("persuasive_outputs_trust_formation", "scratch/persuasive_candidates.txt")
dump_theme("user_evaluation_verification_behavior", "scratch/verification_candidates.txt")
conn.close()
print("Dumps created in scratch/ folder.")
