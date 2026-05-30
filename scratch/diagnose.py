import sqlite3
import math
from pathlib import Path

db_path = Path("data/research.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

THEME_KEYWORDS = {
    "persuasive_outputs_trust_formation": [
        "why users trust", "confidence cues", "persuasive responses", "perceived expertise", 
        "authority signals", "trust formation", "trust", "empathy", "comfort", "confident", 
        "cautious", "caution", "expertise", "authority", "persuasion", "persuasive", "sycophancy", 
        "certainty", "trusting", "credibility", "logical", "logic", "fallacy", "fallacies", 
        "tactic", "tactics", "debate", "defend", "rhetoric", "rhetorical", "manipulation", 
        "sycophant", "relationship", "argument", "convince", "persuade"
    ]
}

def diagnose_post(post_id, theme_slug):
    row = cur.execute("""
        SELECT p.id, p.score, p.title, p.selftext, a.evidence_quote, a.theme_rationale, a.model_confidence
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE p.id = ?
    """, (post_id,)).fetchone()
    
    if not row:
        print(f"Post {post_id} not found!")
        return
        
    title = (row["title"] or "").lower()
    text = (row["selftext"] or "").lower()
    quote = (row["evidence_quote"] or "").lower()
    rationale = (row["theme_rationale"] or "").lower()
    score = row["score"] or 0
    model_conf = row["model_confidence"]
    
    conf_score = model_conf if model_conf is not None else 0.8
    
    keywords = THEME_KEYWORDS.get(theme_slug, [])
    similarity_score = 0.0
    matched_title_quote = []
    matched_body_rationale = []
    for kw in keywords:
        if kw in quote or kw in title:
            similarity_score += 2.5
            matched_title_quote.append(kw)
        elif kw in text or kw in rationale:
            similarity_score += 0.4
            matched_body_rationale.append(kw)
            
    raw_similarity = similarity_score
    similarity_score = min(similarity_score, 6.0)
    
    rationale_len = len(rationale)
    len_score = min(rationale_len / 150.0, 1.5)
    
    ANALYTICAL_CONNECTORS = ["because", "demonstrates", "highlights", "shows", "illustrates", "indicates", "explains", "leads", "causes", "consequence", "impact", "reflects", "reveals", "exhibits", "documents"]
    connector_score = 0.0
    matched_connectors = []
    for conn_word in ANALYTICAL_CONNECTORS:
        if conn_word in rationale:
            connector_score += 0.2
            matched_connectors.append(conn_word)
    connector_score = min(connector_score, 1.0)
    
    reddit_influence = 0.01 * math.log(score + 1)
    
    meta_indicators = [
        "list", "reasons", "manifesto", "comparison", "alternative", "asked chatgpt", "asked chat gpt", 
        "what do you think", "versus", "vs", "fanfic", "write a", "fix seasons", "seasons 7", 
        "how it would look", "future looks like", "rules.txt", "ai partner", "fiction", 
        "fictional", "story", "stories", "game of thrones", "prompt guide", "instructions for", "PSA:",
        "door closes", "neon-lit", "digital family"
    ]
    penalty = 0.0
    matched_penalties = []
    for indicator in meta_indicators:
        if indicator in title or indicator in text[:200]:
            penalty += 3.0
            matched_penalties.append(indicator)
            
    total = (conf_score * 2.0) + similarity_score + (len_score + connector_score) + reddit_influence - penalty
    
    print(f"\nDIAGNOSIS FOR {post_id}:")
    print(f"Title: {row['title']}")
    print(f"Confidence: {model_conf} -> Conf Component: {conf_score * 2.0:.2f}")
    print(f"Matched Title/Quote Keywords: {matched_title_quote}")
    print(f"Matched Body/Rationale Keywords: {matched_body_rationale}")
    print(f"Raw Similarity: {raw_similarity:.2f} -> Capped Similarity Component: {similarity_score:.2f}")
    print(f"Rationale Length: {rationale_len} -> Len Component: {len_score:.2f}")
    print(f"Matched Connectors: {matched_connectors} -> Connector Component: {connector_score:.2f}")
    print(f"Reddit Score: {score} -> Reddit Component: {reddit_influence:.4f}")
    print(f"Matched Penalties: {matched_penalties} -> Penalty Component: -{penalty:.2f}")
    print(f"TOTAL SCORE: {total:.4f}")

diagnose_post("1slcgpx", "persuasive_outputs_trust_formation")
diagnose_post("1tn0y1h", "persuasive_outputs_trust_formation")

conn.close()
