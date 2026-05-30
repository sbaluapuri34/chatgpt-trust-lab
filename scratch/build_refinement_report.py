import json
from pathlib import Path

# Load final quotes
quotes_path = Path("data/aggregated/representative_quotes.json")
if not quotes_path.exists():
    print("Quotes JSON not found!")
    exit(1)

with quotes_path.open(encoding="utf-8") as f:
    quotes_data = json.load(f)

# Set custom order
theme_order = [
    "overconfident_incorrect_outputs",
    "user_trust_breakdown",
    "over_reliance_on_ai_outputs",
    "user_evaluation_verification_behavior",
    "real_world_impact_of_ai_outputs",
    "persuasive_outputs_trust_formation"
]

theme_labels = {
    "overconfident_incorrect_outputs": "Confidently Incorrect Outputs",
    "user_trust_breakdown": "User Trust Breakdown",
    "over_reliance_on_ai_outputs": "Over-Reliance on AI Outputs",
    "user_evaluation_verification_behavior": "User Evaluation & Verification Behavior",
    "real_world_impact_of_ai_outputs": "Real-World Impact of AI Outputs",
    "persuasive_outputs_trust_formation": "Persuasive Outputs & Trust Formation"
}

content = """# Dashboard Refinement Report
*Alignment Report for ChatGPT Output Trust & Evaluation Lab*

This report confirms the implementation of presentation-layer alignments and representative quote refinement in the dashboard. The changes improve qualitative clarity and strengthen the narrative flow to map directly to the Product Management assignment objectives.

---

## 🧭 Final Dropdown & Navigation Order

To reflect the user journey of interacting with ChatGPT, the dashboard dropdowns, filters, tabs, legends, and selectors have been reordered into the following sequence:

1. **Confidently Incorrect Outputs** (`overconfident_incorrect_outputs`) — *The trigger event (AI failure)*
2. **User Trust Breakdown** (`user_trust_breakdown`) — *The immediate cognitive response (erosion of trust)*
3. **Over-Reliance on AI Outputs** (`over_reliance_on_ai_outputs`) — *The negative behavioral adaptation (blind trust/attachment)*
4. **User Evaluation & Verification Behavior** (`user_evaluation_verification_behavior`) — *The correction strategy (auditing, fact-checking)*
5. **Real-World Impact of AI Outputs** (`real_world_impact_of_ai_outputs`) — *The tangible consequences (legal, financial, security, health)*
6. **Persuasive Outputs & Trust Formation** (`persuasive_outputs_trust_formation`) — *The underlying psychological drivers (authority signals, simulated empathy)*

---

## 💬 Final Selected Representative Quotes

Here are the top representative quotes displayed under each primary theme in the dashboard. This selection prioritizes semantic relevance, classification confidence, and rationale quality over raw upvotes.

"""

for slug in theme_order:
    label = theme_labels.get(slug, slug)
    content += f"### {label} (`{slug}`)\n\n"
    
    theme_quotes = quotes_data.get(slug, [])
    if not theme_quotes:
        content += "*No quotes available.*\n\n"
        continue
        
    for idx, q in enumerate(theme_quotes):
        content += f"{idx+1}. **Evidence Quote**: *\"{q['evidence_quote'].strip()}\"*\n"
        content += f"   * **Engagement Score**: {q['score']} | **Weight**: {q['weight']}\n"
        content += f"   * **LLM Rationale**: {q['theme_rationale'].strip()}\n"
        content += f"   * **Post Link**: [Original Post]({q['url']})\n\n"
    content += "---\n\n"

content += """## 📋 Rationale for Recent Quote Replacements

Based on user feedback, we audited and refined the selections for the target themes to maximize alignment with the assignment objectives:

### 1. Real-World Impact of AI Outputs
*   **Replacement of positive outcomes**: We audited the top quotes to focus strictly on negative, high-stakes consequences (financial, legal, safety, security).
*   **Excluding custody victory**: The post *"I Won Full Custody With No Lawyer Thanks to ChatGPT"* (ID: `1ovafq9`) was removed. While it demonstrates real-world impact, it represents a positive outcome rather than a negative consequence. It was replaced with **ID: `1rjxeb0`**: *"ChatGPT reportedly submitted a CyberTipline report to the National Center for Missing & Exploited Children"*, exposing a critical automated security reporting escalation that led to disciplinary proceedings for a therapist.
*   **Excluding lawsuit victory**: The post *"ChatGPT is a terrible attorney, but it still helped me win a lawsuit."* (ID: `1oons00`) was replaced with **ID: `1tmq26u`** detailing legally questionable business practices and developer account bans.
*   **Resulting Purity**: The top 5 quotes now focus entirely on major negative outcomes:
    1. **$5M Estate Fraud** (financial misconduct/exposed fraud)
    2. **Near-miss Euthanasia of a Cat** (critical health/veterinary decision-making)
    3. **Mata vs Avianca Court Case** (famous legal case involving fabricated cites)
    4. **Unjust Account/Developer Ban** (loss of dev access/professional impact)
    5. **Therapist Police/CyberTipline Report** (high-stakes automated security reporting)

### 2. User Evaluation & Verification Behavior
*   We replaced prompt instruction sets and custom configurations with actual stories of double-checking and auditing behavior.
*   Surfaced active verification tools like **VerifyAI** (Chrome extension to fact-check LLMs) and documented academic grade double-checking behavior.

### 3. Persuasive Outputs & Trust Formation
*   We removed creative writing fixes and philosophical manifestos.
*   Surfaced ChatGPT's sophisticated fallacies (strawman rebuttals used to defend incorrect outputs), self-reflections on caution calibration ("I can sound confident even when I should be more cautious"), and studies regarding sycophancy in value-laden domains.

---

## 🛡️ Compliance & Data Integrity Confirmation

We confirm the following constraints have been strictly adhered to during this refinement:

*   **No Classifications Changed**: The SQLite database (`data/research.db`) records were not modified, and no post classifications were altered.
*   **No Theme Counts Changed**: The overall counts, percentages, and metrics for each theme remain 100% identical.
*   **No Phase 3 Rerun Occurred**: No LLM processing or Phase 3 pipelines were run. The refinement was conducted entirely at the presentation/aggregation layer by adjusting scoring filters and sorting rules.
"""

output_path = Path("docs/DASHBOARD_REFINEMENT_REPORT.md")
output_path.write_text(content, encoding="utf-8")
print("DASHBOARD_REFINEMENT_REPORT.md built successfully!")
