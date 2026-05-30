import sqlite3
from pathlib import Path

def main():
    db_path = Path("data/research.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
        SELECT p.id, p.score, p.title, a.evidence_quote, a.theme_rationale, a.model_confidence
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = 'real_world_impact_of_ai_outputs'
        ORDER BY p.score DESC
    """
    rows = cur.execute(query).fetchall()
    print(f"Total posts in real_world_impact_of_ai_outputs: {len(rows)}")
    for idx, r in enumerate(rows):
        print(f"{idx+1}. ID: {r['id']} | Score: {r['score']} | Conf: {r['model_confidence']}")
        print(f"   Title: {r['title']}")
        print(f"   Quote: {r['evidence_quote']}")
        print(f"   Rationale: {r['theme_rationale']}")
        print("-" * 50)
    conn.close()

if __name__ == "__main__":
    main()
