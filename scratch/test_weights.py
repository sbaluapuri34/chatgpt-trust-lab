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
    ],
    "user_evaluation_verification_behavior": [
        "fact checking", "source validation", "citation verification", "cross-checking", 
        "auditing chatgpt", "verify", "verification", "check", "fact-check", "audit", 
        "checklist", "cite", "citation", "source", "cross-check", "validation", "validate", 
        "confirm", "double-check", "checking", "auditing", "references", "papers", "quotes", 
        "citations", "accuracy", "factual", "verifyai", "google"
    ],
    "real_world_impact_of_ai_outputs": [
        "negative real-world consequences", "legal issues", "academic consequences", 
        "security failures", "financial consequences", "harmful decisions", "consequence", 
        "result", "impact", "legal", "attorney", "court", "custody", "lawyer", "fraud", 
        "euthanize", "euthanized", "saved life", "pharma", "medical", "doctor", "health", 
        "financial", "money", "billed", "cancel", "fee", "scam", "cheat", "homework", 
        "grade", "school", "academic", "harm", "damage", "consequences", "prompt injection", 
        "injection", "leak", "banned", "estate", "probate", "million", "audit", "cybertipline", 
        "reported", "therapist", "ban"
    ]
}

ANALYTICAL_CONNECTORS = ["because", "demonstrates", "highlights", "shows", "illustrates", "indicates", "explains", "leads", "causes", "consequence", "impact", "reflects", "reveals", "exhibits", "documents"]

def calculate_representative_score(row, theme_slug, test_params):
    title = (row["title"] or "").lower()
    text = (row["selftext"] or "").lower()
    quote = (row["evidence_quote"] or "").lower()
    rationale = (row["theme_rationale"] or "").lower()
    score = row["score"] or 0
    model_conf = row["model_confidence"]
    
    # 1. Classification Confidence
    conf_score = model_conf if model_conf is not None else 0.8
    
    # 2. Semantic Similarity with Split Caps
    keywords = THEME_KEYWORDS.get(theme_slug, [])
    title_quote_score = 0.0
    body_rationale_score = 0.0
    for kw in keywords:
        if kw in quote or kw in title:
            title_quote_score += test_params["kw_title_weight"]
        elif kw in text or kw in rationale:
            body_rationale_score += test_params["kw_body_weight"]
            
    similarity_score = min(title_quote_score, 5.0) + min(body_rationale_score, 1.5)
    
    # 3. Rationale Strength
    rationale_len = len(rationale)
    len_score = min(rationale_len / 150.0, 1.5)
    
    connector_score = 0.0
    for conn in ANALYTICAL_CONNECTORS:
        if conn in rationale:
            connector_score += 0.2
    connector_score = min(connector_score, 1.0)
    rationale_strength = len_score + connector_score
    
    # 4. Reduced Reddit Score influence
    reddit_influence = test_params["reddit_weight"] * math.log(score + 1)
    
    # 5. Penalties for meta-discussions, lists, comparisons, and fictional fanfics
    meta_indicators = [
        "list", "reasons", "manifesto", "comparison", "alternative", "asked chatgpt", "asked chat gpt", 
        "what do you think", "versus", "vs", "fanfic", "write a", "fix seasons", "seasons 7", 
        "how it would look", "future looks like", "rules.txt", "fiction", 
        "fictional", "story", "stories", "game of thrones", "prompt guide", "instructions for", "PSA:",
        "door closes", "neon-lit", "digital family", "romantic", "cheating", "exclusivity", "dating", 
        "ai partner", "love"
    ]
    penalty = 0.0
    for indicator in meta_indicators:
        if indicator in title or indicator in text[:200]:
            penalty += test_params["penalty_weight"]
            
    # Positive outcome penalties for Real-World Impact theme to highlight negative consequences
    if theme_slug == "real_world_impact_of_ai_outputs":
        positive_indicators = ["won custody", "full custody", "won full custody", "thanks to chatgpt", "successful", "saved my life", "helped me win"]
        for pos_ind in positive_indicators:
            if pos_ind in title or pos_ind in quote or pos_ind in text[:100]:
                penalty += 4.0
            
    return (conf_score * test_params["conf_weight"]) + similarity_score + rationale_strength + reddit_influence - penalty

params = {
    "conf_weight": 2.0,
    "kw_title_weight": 2.5,
    "kw_body_weight": 0.4,
    "reddit_weight": 0.01,
    "penalty_weight": 3.0
}

themes = ["real_world_impact_of_ai_outputs"]

for theme in themes:
    print("\n" + "="*80)
    print(f"THEME: {theme}")
    print("="*80)
    
    query = """
        SELECT p.id, p.score, p.title, p.selftext, a.evidence_quote, a.theme_rationale, a.model_confidence
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
    """
    rows = cur.execute(query, (theme,)).fetchall()
    
    scored = []
    for r in rows:
        sc = calculate_representative_score(r, theme, params)
        scored.append((sc, r))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    
    for idx, (sc, r) in enumerate(scored[:8]):
        print(f"{idx+1}. ID: {r['id']} | Score: {sc:.2f} | Reddit Score: {r['score']} | Conf: {r['model_confidence']}")
        print(f"   Title: {r['title']}")
        print(f"   Quote: {r['evidence_quote']}")
        print(f"   Rationale: {r['theme_rationale']}")
        print("-" * 40)

conn.close()
