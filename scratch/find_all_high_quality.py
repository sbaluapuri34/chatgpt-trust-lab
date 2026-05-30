import sqlite3
import json
import sys
from pathlib import Path

def main():
    # Force utf-8 output in Windows console if supported, otherwise replace characters
    sys.stdout.reconfigure(encoding='utf-8')
    
    db_path = Path("data/research.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=== Persuasive Outputs & Trust Formation Candidates ===")
    query1 = """
        SELECT p.id, p.score, p.title, a.evidence_quote, a.theme_rationale
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = 'persuasive_outputs_trust_formation'
        ORDER BY p.score DESC
    """
    rows1 = cur.execute(query1).fetchall()
    for idx, r in enumerate(rows1[:25]):
        print(f"{idx+1}. ID: {r['id']} | Score: {r['score']}")
        print(f"   Title: {r['title']}")
        print(f"   Quote: {r['evidence_quote']}")
        print(f"   Rationale: {r['theme_rationale']}")
        print("-" * 50)
        
    print("\n=== User Evaluation & Verification Behavior Candidates ===")
    query2 = """
        SELECT p.id, p.score, p.title, a.evidence_quote, a.theme_rationale
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = 'user_evaluation_verification_behavior'
        ORDER BY p.score DESC
    """
    rows2 = cur.execute(query2).fetchall()
    for idx, r in enumerate(rows2[:25]):
        print(f"{idx+1}. ID: {r['id']} | Score: {r['score']}")
        print(f"   Title: {r['title']}")
        print(f"   Quote: {r['evidence_quote']}")
        print(f"   Rationale: {r['theme_rationale']}")
        print("-" * 50)
        
    conn.close()

if __name__ == "__main__":
    main()
