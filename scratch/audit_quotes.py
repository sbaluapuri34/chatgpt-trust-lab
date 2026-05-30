import sqlite3
import sys

# Reconfigure stdout to use utf-8
sys.stdout.reconfigure(encoding='utf-8')

def audit_theme(theme_slug):
    conn = sqlite3.connect('data/research.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
        SELECT p.id, p.score, p.title, p.selftext, a.evidence_quote, a.theme_rationale
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
        ORDER BY p.score DESC
    """
    rows = cur.execute(query, (theme_slug,)).fetchall()
    print(f"=== THEME: {theme_slug} (Found {len(rows)} posts) ===")
    for idx, r in enumerate(rows):
        print(f"Index: {idx+1}")
        print(f"ID: {r['id']}")
        print(f"Score: {r['score']}")
        print(f"Title: {r['title']}")
        print(f"Quote: {r['evidence_quote']}")
        print(f"Rationale: {r['theme_rationale']}")
        print(f"Excerpt: {(r['selftext'] or '')[:200].replace('\n', ' ')}...")
        print("-" * 60)
    conn.close()

print("AUDITING PERSUASIVE OUTPUTS & TRUST FORMATION")
audit_theme("persuasive_outputs_trust_formation")

print("\n" + "="*80 + "\n")

print("AUDITING USER EVALUATION & VERIFICATION BEHAVIOR")
audit_theme("user_evaluation_verification_behavior")
