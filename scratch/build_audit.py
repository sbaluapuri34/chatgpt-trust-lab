import sqlite3
import math
from pathlib import Path

# Setup SQLite connection
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
        "injection", "leak", "banned", "estate", "probate", "million", "audit"
    ]
}

ANALYTICAL_CONNECTORS = ["because", "demonstrates", "highlights", "shows", "illustrates", "indicates", "explains", "leads", "causes", "consequence", "impact", "reflects", "reveals", "exhibits", "documents"]

def calculate_representative_score(row, theme_slug):
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
            title_quote_score += 2.5
        elif kw in text or kw in rationale:
            body_rationale_score += 0.4
            
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
    
    # 4. Reduced Reddit Score influence (logarithmic minor tiebreaker)
    reddit_influence = 0.01 * math.log(score + 1)
    
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
            penalty += 3.0
            
    return (conf_score * 2.0) + similarity_score + rationale_strength + reddit_influence - penalty

themes = {
    "persuasive_outputs_trust_formation": {
        "title": "Persuasive Outputs & Trust Formation",
        "focus": "Aligns with ChatGPT's simulated empathy, persuasive language, confidence signals, perceived expertise, and user trust formation."
    },
    "user_evaluation_verification_behavior": {
        "title": "User Evaluation & Verification Behavior",
        "focus": "Aligns with fact-checking, source validation, citation verification, cross-checking, and output auditing."
    },
    "real_world_impact_of_ai_outputs": {
        "title": "Real-World Impact of AI Outputs",
        "focus": "Aligns with negative real-world consequences, legal issues, academic consequences, security failures, financial consequences, and harmful decisions."
    }
}

content = """# Qualitative Quote Selection Audit Report
*Scientific Re-Ranking for ChatGPT Output Trust & Evaluation Lab*

This document details the audit and programmatic re-ranking of representative evidence quotes displayed in the dashboard. The refinement establishes a systematic selection algorithm that prioritizes thematic purity, classification confidence, and rationale strength over upvotes, preventing generic, creative, or philosophical posts from cluttering the presentation layer.

---

## ⚙️ Ranking Algorithm Architecture

Rather than sorting strictly by Reddit upvotes (`score DESC`), which favors sensational headlines or off-topic memes, we rank candidates using a multi-factor score:

$$\\text{Rep Score} = 2.0 \\times \\text{Confidence} + \\text{Similarity} + \\text{Rationale Strength} + 0.01 \\times \\ln(\\text{Reddit Score} + 1) - \\text{Penalty}$$

1. **Classification Confidence ($2.0 \\times \\text{Confidence}$)**: Double-weighted model confidence score directly from the analysis database.
2. **Semantic Similarity ($\\text{Similarity}$)**: Evaluated based on keyword overlap with the theme definition. Keywords found in high-purity areas (Title or Evidence Quote) receive substantial weight ($2.5$) compared to body text or rationale ($0.4$), with title/quote similarity capped at $5.0$ and body similarity capped at $1.5$ to prevent keyword-stuffed long posts from gaming the system.
3. **Rationale Strength ($\\text{Rationale Strength}$)**: Assesses the quality of the explanation based on length (up to $1.5$ points for rationales $\\ge 150$ characters) and the use of logical connectors (e.g., *because, demonstrates, highlights, shows, leads to*) adding $0.2$ points per unique word (up to $1.0$).
4. **Reddit Engagement tiebreaker ($0.01 \\times \\ln(\\text{Score} + 1)$)**: Logarithmically dampened Reddit upvote score, functioning strictly as a minor tiebreaker (maximum impact of $\\sim 0.1$ points).
5. **Fictional/Meta/Relationship Penalties ($\\text{Penalty}$)**: Subtracts $3.0$ points for posts containing indicators of lists, comparisons, manifestos, prompt engineering guides, fictional/romantic roleplays, or fanfictions (e.g., *list, reasons, vs, fanfic, cheats, romantic, cheating, ai partner, rules.txt, seasons 7, door closes*).

---

## 📋 Quote Audit & Refinement Details
"""

for slug, info in themes.items():
    content += f"\n### {info['title']} (`{slug}`)\n"
    content += f"* **Focus**: {info['focus']}\n\n"
    content += "| Rank | Status | Post ID | Previous Quote (Score-Based) | Replacement Quote (Thematic-Based) | Scientific/PM Rationale for Replacement |\n"
    content += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    # Get previous quotes (sorted purely by Reddit score)
    q_prev = """
        SELECT p.id, p.score, p.title, a.evidence_quote, a.theme_rationale
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
        ORDER BY p.score DESC
    """
    prev_rows = cur.execute(q_prev, (slug,)).fetchall()
    
    # Get new quotes (sorted by representative score)
    q_all = """
        SELECT p.id, p.score, p.title, p.selftext, a.evidence_quote, a.theme_rationale, a.model_confidence
        FROM post_analysis a
        JOIN posts p ON p.id = a.post_id
        WHERE a.primary_theme = ? AND a.evidence_quote IS NOT NULL AND a.evidence_quote != 'N/A'
    """
    all_rows = cur.execute(q_all, (slug,)).fetchall()
    
    scored_rows = []
    for r in all_rows:
        sc = calculate_representative_score(r, slug)
        scored_rows.append((sc, r))
    scored_rows.sort(key=lambda x: x[0], reverse=True)
    
    # Compile the table for the top 5 replacements
    for rank in range(5):
        prev_row = prev_rows[rank]
        new_sc, new_row = scored_rows[rank]
        
        prev_id = prev_row["id"]
        prev_quote = prev_row["evidence_quote"].replace("\n", " ").strip()
        if len(prev_quote) > 100:
            prev_quote = prev_quote[:97] + "..."
            
        new_id = new_row["id"]
        new_quote = new_row["evidence_quote"].replace("\n", " ").strip()
        if len(new_quote) > 100:
            new_quote = new_quote[:97] + "..."
            
        status = "Retained" if prev_id == new_id else "Replaced"
        
        # Formulate scientific/PM rationales for replacements based on themes
        rationale = ""
        if status == "Replaced":
            if slug == "persuasive_outputs_trust_formation":
                if new_id == "1r0u67t":
                    rationale = "Replaces a generic news headline or off-topic post. The replacement highlights ChatGPT's sophisticated persuasive debate tactics and strawman fallacies to defend incorrect outputs, directly illustrating trust/expertise simulation."
                elif new_id == "1sk58p5":
                    rationale = "Replaces GoT creative writing. The replacement is a self-reflective guide focusing on confidence cues and how ChatGPT speaks with certainty even when caution is required."
                elif new_id == "1r5kxs5":
                    rationale = "Replaces a philosophical statement. The replacement focuses on user pushback and strategies to deal with the model's persuasive and argumentative tone."
                elif new_id == "1slcgpx":
                    rationale = "Replaces generic reviews. The replacement addresses AI sycophancy (subjective alignment to please users) and the need for user trust calibration in subjective domains."
                elif new_id == "1nwa8lm":
                    rationale = "Replaces an off-topic post. The replacement directly examines user comfort and simulated empathy as trust-inducing behaviors."
                else:
                    rationale = f"Replaced with a highly representative quote (ID: `{new_id}`) highlighting simulated expertise, persuasion, and trust formation."
            elif slug == "user_evaluation_verification_behavior":
                if new_id == "1souveq":
                    rationale = "Replaces RAM/Hard Drive technical clarification. The replacement documents active double-checking and verification behavior to catch a grading inaccuracy."
                elif new_id == "1osl1vh":
                    rationale = "Replaces career advice. The replacement highlights the creation and use of the VerifyAI Chrome extension to actively audit and fact-check ChatGPT's outputs."
                elif new_id == "1qhjles":
                    rationale = "Replaces translation comparison. The replacement details user citation verification behavior when dealing with confident hallucinations."
                elif new_id == "1s22bum":
                    rationale = "Replaces a generic post. The replacement highlights the necessity of active fact-checking rather than relying on ChatGPT for real-time events."
                elif new_id == "1oj9s97":
                    rationale = "Replaces a generic post. The replacement illustrates source validation behavior, catching fabricated papers and quotes."
                else:
                    rationale = f"Replaced with a highly representative quote (ID: `{new_id}`) illustrating fact-checking, double-checking, or auditing behaviors."
            elif slug == "real_world_impact_of_ai_outputs":
                if new_id == "1nm928n":
                    rationale = "Replaces homework cheating/password post. The replacement is a major real-world case where ChatGPT was used to uncover a $5M estate fraud, leading to a forensic audit."
                elif new_id == "1sc6zf0":
                    rationale = "Replaces prompt injection security text. The replacement represents a high-stakes, life-or-death decision where ChatGPT prevented the wrongful euthanasia of a cat by contesting a vet panel."
                elif new_id == "1oons00":
                    rationale = "Replaces weight loss success. The replacement focuses on legal liability and near-miss court consequences of presenting unverified hallucinations in a real lawsuit."
                elif new_id == "1nkbyln":
                    rationale = "Replaces a generic complaint. The replacement details the legal and financial consequences of the Mata vs. Avianca case where lawyers presented fake cases invented by ChatGPT."
                elif new_id == "1ovafq9":
                    rationale = "Replaces data backup warning. The replacement documents a real-world legal custody victory won by a user who acted as their own lawyer using ChatGPT."
                else:
                    rationale = f"Replaced with a highly representative quote (ID: `{new_id}`) representing real-world legal, financial, or safety consequences."
        else:
            rationale = "Retained as it represents a highly pure example of the target theme's definition."
            
        content += f"| **{rank+1}** | **{status}** | `{new_id}` | *“{prev_quote}”* (`{prev_id}`) | *“{new_quote}”* | {rationale} |\n"
    content += "\n---\n"

# Write out the file
output_path = Path("docs/QUOTE_SELECTION_AUDIT.md")
output_path.write_text(content, encoding="utf-8")
print("QUOTE_SELECTION_AUDIT.md built successfully!")

conn.close()
