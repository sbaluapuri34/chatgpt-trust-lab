import sqlite3
import json
import sys
from pathlib import Path

def main():
    db_path = Path("data/research.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    out_file = Path("scratch/top_candidates_report.txt")
    
    with out_file.open("w", encoding="utf-8") as f:
        f.write("=== CANDIDATES AUDIT REPORT ===\n\n")
        
        # PERSUASIVE
        f.write("=== Persuasive Outputs & Trust Formation ===\n\n")
        query1 = """
            SELECT p.id, p.score, p.title, a.evidence_quote, a.theme_rationale
            FROM post_analysis a
            JOIN posts p ON p.id = a.post_id
            WHERE a.primary_theme = 'persuasive_outputs_trust_formation'
            ORDER BY p.score DESC
        """
        rows1 = cur.execute(query1).fetchall()
        for idx, r in enumerate(rows1):
            f.write(f"Index: {idx+1}\n")
            f.write(f"ID: {r['id']}\n")
            f.write(f"Score: {r['score']}\n")
            f.write(f"Title: {r['title']}\n")
            f.write(f"Quote: {r['evidence_quote']}\n")
            f.write(f"Rationale: {r['theme_rationale']}\n")
            f.write("-" * 80 + "\n")
            
        f.write("\n\n=== User Evaluation & Verification Behavior ===\n\n")
        query2 = """
            SELECT p.id, p.score, p.title, a.evidence_quote, a.theme_rationale
            FROM post_analysis a
            JOIN posts p ON p.id = a.post_id
            WHERE a.primary_theme = 'user_evaluation_verification_behavior'
            ORDER BY p.score DESC
        """
        rows2 = cur.execute(query2).fetchall()
        for idx, r in enumerate(rows2):
            f.write(f"Index: {idx+1}\n")
            f.write(f"ID: {r['id']}\n")
            f.write(f"Score: {r['score']}\n")
            f.write(f"Title: {r['title']}\n")
            f.write(f"Quote: {r['evidence_quote']}\n")
            f.write(f"Rationale: {r['theme_rationale']}\n")
            f.write("-" * 80 + "\n")
            
    conn.close()
    print("Candidates written to scratch/top_candidates_report.txt successfully.")

if __name__ == "__main__":
    main()
