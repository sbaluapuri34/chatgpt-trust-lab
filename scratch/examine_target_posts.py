import sqlite3
import json
from pathlib import Path

def main():
    db_path = Path("data/research.db")
    if not db_path.exists():
        print("Database not found!")
        return
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    target_ids = ["1nwa8lm", "1sk58p5", "1oj9s97", "1tdijbl"]
    
    query = """
        SELECT p.id, p.title, p.score, p.weight, p.url, a.primary_theme, a.evidence_quote, a.theme_rationale
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE p.id IN ({})
    """.format(",".join("?" for _ in target_ids))
    
    rows = cur.execute(query, target_ids).fetchall()
    conn.close()
    
    print(f"Found {len(rows)} matching posts in DB.")
    for idx, r in enumerate(rows):
        print(f"--- POST {idx+1}: {r['id']} ---")
        print(f"Title: {r['title']}")
        print(f"Score: {r['score']}")
        print(f"Weight: {r['weight']}")
        print(f"URL: {r['url']}")
        print(f"Theme: {r['primary_theme']}")
        print(f"Quote: {r['evidence_quote']}")
        print(f"Rationale: {r['theme_rationale']}")
        print()

if __name__ == "__main__":
    main()
