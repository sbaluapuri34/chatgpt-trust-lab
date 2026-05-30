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
    
    # Query posts under the audited themes
    query = """
        SELECT p.id, p.title, p.score, a.primary_theme, a.secondary_themes, a.evidence_quote, a.theme_rationale
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme IN ('confidence_signals_persuasive_communication', 'mixed_or_multitheme')
    """
    rows = cur.execute(query).fetchall()
    conn.close()
    
    print(f"Found {len(rows)} posts to audit.")
    
    # Save to a json file in scratch for detailed inspection
    out_path = Path("scratch/posts_to_audit.json")
    out_path.parent.mkdir(exist_ok=True)
    
    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "title": r["title"],
            "score": r["score"],
            "primary_theme": r["primary_theme"],
            "secondary_themes": json.loads(r["secondary_themes"] or "[]"),
            "evidence_quote": r["evidence_quote"],
            "theme_rationale": r["theme_rationale"]
        })
        
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Dumped audit posts to {out_path}")

if __name__ == "__main__":
    main()
