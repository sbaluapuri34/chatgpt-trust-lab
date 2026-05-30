# Qualitative Quote Selection Audit Report
*Scientific Re-Ranking for ChatGPT Output Trust & Evaluation Lab*

This document details the audit and programmatic re-ranking of representative evidence quotes displayed in the dashboard. The refinement establishes a systematic selection algorithm that prioritizes thematic purity, classification confidence, and rationale strength over upvotes, preventing generic, creative, or philosophical posts from cluttering the presentation layer.

---

## ⚙️ Ranking Algorithm Architecture

Rather than sorting strictly by Reddit upvotes (`score DESC`), which favors sensational headlines or off-topic memes, we rank candidates using a multi-factor score:

$$\text{Rep Score} = 2.0 \times \text{Confidence} + \text{Similarity} + \text{Rationale Strength} + 0.01 \times \ln(\text{Reddit Score} + 1) - \text{Penalty}$$

1. **Classification Confidence ($2.0 \times \text{Confidence}$)**: Double-weighted model confidence score directly from the analysis database.
2. **Semantic Similarity ($\text{Similarity}$)**: Evaluated based on keyword overlap with the theme definition. Keywords found in high-purity areas (Title or Evidence Quote) receive substantial weight ($2.5$) compared to body text or rationale ($0.4$), with title/quote similarity capped at $5.0$ and body similarity capped at $1.5$ to prevent keyword-stuffed long posts from gaming the system.
3. **Rationale Strength ($\text{Rationale Strength}$)**: Assesses the quality of the explanation based on length (up to $1.5$ points for rationales $\ge 150$ characters) and the use of logical connectors (e.g., *because, demonstrates, highlights, shows, leads to*) adding $0.2$ points per unique word (up to $1.0$).
4. **Reddit Engagement tiebreaker ($0.01 \times \ln(\text{Score} + 1)$)**: Logarithmically dampened Reddit upvote score, functioning strictly as a minor tiebreaker (maximum impact of $\sim 0.1$ points).
5. **Fictional/Meta/Relationship Penalties ($\text{Penalty}$)**: Subtracts $3.0$ points for posts containing indicators of lists, comparisons, manifestos, prompt engineering guides, fictional/romantic roleplays, or fanfictions (e.g., *list, reasons, vs, fanfic, cheats, romantic, cheating, ai partner, rules.txt, seasons 7, door closes*).

---

## 📋 Quote Audit & Refinement Details

### Persuasive Outputs & Trust Formation (`persuasive_outputs_trust_formation`)
* **Focus**: Aligns with ChatGPT's simulated empathy, persuasive language, confidence signals, perceived expertise, and user trust formation.

| Rank | Status | Post ID | Previous Quote (Score-Based) | Replacement Quote (Thematic-Based) | Scientific/PM Rationale for Replacement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Replaced** | `1r0u67t` | *“Man stole Reddit’s homework and got 800M users”* (`1o3yoka`) | *“ChatGPT 5.2 at times misrepresented the user’s position to rebut a weaker claim.”* | Replaces a generic news headline or off-topic post. The replacement highlights ChatGPT's sophisticated persuasive debate tactics and strawman fallacies to defend incorrect outputs, directly illustrating trust/expertise simulation. |
| **2** | **Replaced** | `1sk58p5` | *“Power corrupts Love and duty are incompatible Prophecy is dangerous The real enemy is human natur...”* (`1tnoaf8`) | *“I can sound confident even when I should be more cautious.”* | Replaces GoT creative writing. The replacement is a self-reflective guide focusing on confidence cues and how ChatGPT speaks with certainty even when caution is required. |
| **3** | **Replaced** | `1r5kxs5` | *“You don’t conquer reality. You cooperate with it—or you pay rent in suffering.”* (`1qejwm1`) | *“Stop trying to persuade the model. Automate the management.”* | Replaces a philosophical statement. The replacement focuses on user pushback and strategies to deal with the model's persuasive and argumentative tone. |
| **4** | **Replaced** | `1slcgpx` | *“So perhaps it's not so much that people are "fooled" by a machine, but rather, people now find re...”* (`1nwa8lm`) | *“The practical takeaway isn't necessarily "switch models." It's being more skeptical of AI respons...”* | Replaces generic reviews. The replacement addresses AI sycophancy (subjective alignment to please users) and the need for user trust calibration in subjective domains. |
| **5** | **Replaced** | `1nwa8lm` | *“I have been using both the free and paid versions of ChatGPT for over a year, so I have seen how ...”* (`1ssgsri`) | *“So perhaps it's not so much that people are "fooled" by a machine, but rather, people now find re...”* | Replaces an off-topic post. The replacement directly examines user comfort and simulated empathy as trust-inducing behaviors. |

---

### User Evaluation & Verification Behavior (`user_evaluation_verification_behavior`)
* **Focus**: Aligns with fact-checking, source validation, citation verification, cross-checking, and output auditing.

| Rank | Status | Post ID | Previous Quote (Score-Based) | Replacement Quote (Thematic-Based) | Scientific/PM Rationale for Replacement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Replaced** | `1souveq` | *“You are confusing RAM with a Hard Drive.”* (`1r1b3gl`) | *“I double-checked everything and saw my work was good, but he kept pressuring me.”* | Replaces RAM/Hard Drive technical clarification. The replacement documents active double-checking and verification behavior to catch a grading inaccuracy. |
| **2** | **Replaced** | `1osl1vh` | *“Chatgpt helped me figure out WHY I couldn't decide, which really helped me make a more informed d...”* (`1or0xz2`) | *“ChatGPT hallucinated again, so I built VerifyAI it checks if your AI’s answer is actually true.  You”* | Replaces career advice. The replacement highlights the creation and use of the VerifyAI Chrome extension to actively audit and fact-check ChatGPT's outputs. |
| **3** | **Replaced** | `1qhjles` | *“i’ve caught it making up papers or quotes that don’t exist”* (`1oj9s97`) | *“Ask ChatGPT to cite its sources for more reliable info  I've gotten so frustrated with its confident”* | Replaces translation comparison. The replacement details user citation verification behavior when dealing with confident hallucinations. |
| **4** | **Replaced** | `1s22bum` | *“Le Chat nails the subtle linguistic and (sub-)cultural differences, especially for multilingual E...”* (`1r219sd`) | *“Using ChatGPT to fact-check real-time events is how misinformation spreads.”* | Replaces a generic post. The replacement highlights the necessity of active fact-checking rather than relying on ChatGPT for real-time events. |
| **5** | **Replaced** | `1oj9s97` | *“Am I the only one (I am a power user) that is actually still happy with ChatGPT?  I’ve been at home”* (`1qfy995`) | *“i’ve caught it making up papers or quotes that don’t exist”* | Replaces a generic post. The replacement illustrates source validation behavior, catching fabricated papers and quotes. |

---

### Real-World Impact of AI Outputs (`real_world_impact_of_ai_outputs`)
* **Focus**: Aligns with negative real-world consequences, legal issues, academic consequences, security failures, financial consequences, and harmful decisions.

| Rank | Status | Post ID | Previous Quote (Score-Based) | Replacement Quote (Thematic-Based) | Scientific/PM Rationale for Replacement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Replaced** | `1nm928n` | *“Chat GPT just giving away the password I set up so my son wouldn’t use it to cheat on his homework”* (`1ojh5qm`) | *“I used ChatGPT to expose a $5 million estate fraud, get a forensic audit, and uncover 10 years of...”* | Replaces homework cheating/password post. The replacement is a major real-world case where ChatGPT was used to uncover a $5M estate fraud, leading to a forensic audit. |
| **2** | **Replaced** | `1sc6zf0` | *“Docs, emails, Slack history, API responses, anything our agent reads is an attack surface.”* (`1r5snvl`) | *“If I hadn't used chatgpt to explain her condition compared with her actions, I would have just ta...”* | Replaces prompt injection security text. The replacement represents a high-stakes, life-or-death decision where ChatGPT prevented the wrongful euthanasia of a cat by contesting a vet panel. |
| **3** | **Replaced** | `1oons00` | *“I now have noticeably more muscle and look lean.”* (`1sbkr23`) | *“I tried to fact check every single thing ChatGPT came up with so I didnt get stuck presenting hal...”* | Replaces weight loss success. The replacement focuses on legal liability and near-miss court consequences of presenting unverified hallucinations in a real lawsuit. |
| **4** | **Replaced** | `1nkbyln` | *“Whatever they’ve done to 4.0 & 4.1 has made it completely untrustworthy, even for simple tasks.”* (`1ndansj`) | *“The Mata vs Avianca case: lawyers used ChatGPT which invented 6 completely fictional court cases.”* | Replaces a generic complaint. The replacement details the legal and financial consequences of the Mata vs. Avianca case where lawyers presented fake cases invented by ChatGPT. |
| **5** | **Replaced** | `1ovafq9` | *“You obviously can't rely on ChatGPT to back-up your data, so, do so yourself, and religiously, or...”* (`1qpj4ax`) | *“I Won Full Custody With No Lawyer Thanks to ChatGPT.  The fight started 7 years ago when i paid $300”* | Replaces data backup warning. The replacement documents a real-world legal custody victory won by a user who acted as their own lawyer using ChatGPT. |

---
