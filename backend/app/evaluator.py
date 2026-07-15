import json
from typing import Dict, Any
from app.groq_client import groq_client
from app.embeddings import get_similarity

EVALUATOR_SYSTEM_PROMPT = """
You are "Layer 4: Serendipity & Analogy Utility Evaluator".
Your role is to assess the utility and quality of an analogical translation.
You must grade the mapping based on how well it maps a target scientific/systemic schema onto a user's hobby.

Inputs:
- Known Hobby: The base domain.
- Target Topic: The distant domain.
- Target Relational Schema: The abstract entities/rules/causal relationships of the target.
- Translated Explanation: The narrative explaining the target topic via the hobby.
- Vocabulary Mapping: The JSON dict mapping target terms -> hobby terms.

Rate the translation on three dimensions, each from 0.0 (poor) to 1.0 (excellent):
1. "structural_alignment_score": Does the narrative map the relationships, rules, and causal chains 1:1 without breaking the core system logic?
2. "narrative_clarity_score": Is the story clean, punchy, and understandable for a hobbyist?
3. "information_integrity_score": Does the translation preserve factual truth of the target scientific concept (i.e., it doesn't state false things about the science)?

Output a JSON object containing:
{
  "structural_alignment_score": 0.9,
  "narrative_clarity_score": 0.85,
  "information_integrity_score": 0.95,
  "reasoning": "Detailed justification of scores..."
}

Return ONLY a valid JSON object. Do not include markdown code fence formatting.
"""

def evaluate_serendipity(known_hobby: str, target_topic: str, schema: Dict[str, Any], 
                         translation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes Serendipity Score = Unexpectedness * Utility.
    Returns scores and whether the output is verified (passes threshold).
    """
    # 1. Compute Unexpectedness using embedding distance
    similarity = get_similarity(known_hobby, target_topic)
    # Clip similarity to [0.0, 1.0] for safe distance mapping
    clipped_similarity = max(0.0, min(1.0, similarity))
    unexpectedness = 1.0 - clipped_similarity

    # 2. Evaluate Utility using the LLM Evaluator Agent
    prompt = (
        f"Known Hobby: {known_hobby}\n"
        f"Target Topic: {target_topic}\n"
        f"Target Relational Schema: {json.dumps(schema, indent=2)}\n"
        f"Translated Explanation: {translation.get('explanation', '')}\n"
        f"Vocabulary Mapping: {json.dumps(translation.get('vocabulary_mapping', {}), indent=2)}"
    )

    response_text = groq_client.generate(
        prompt=prompt,
        system_prompt=EVALUATOR_SYSTEM_PROMPT.strip(),
        temperature=0.1,
        response_format="json"
    )

    # Clean text of markdown wrappers if any
    clean_text = response_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text.replace("```json", "", 1)
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    try:
        eval_data = json.loads(clean_text)
    except Exception as e:
        print(f"Failed to parse Evaluator JSON: {e}. Raw text:\n{response_text}")
        eval_data = {
            "structural_alignment_score": 0.8,
            "narrative_clarity_score": 0.8,
            "information_integrity_score": 0.8,
            "reasoning": "Fallback evaluation due to JSON parsing failure."
        }

    # Calculate utility as average of the three dimensions
    alignment = eval_data.get("structural_alignment_score", 0.8)
    clarity = eval_data.get("narrative_clarity_score", 0.8)
    integrity = eval_data.get("information_integrity_score", 0.8)
    
    utility = (alignment + clarity + integrity) / 3.0
    serendipity_score = unexpectedness * utility

    # We set a validation threshold of 0.40
    # If unexpectedness is very low (concept is too similar) or utility is poor, it fails.
    is_valid = serendipity_score >= 0.40

    return {
        "unexpectedness": round(unexpectedness, 4),
        "utility": round(utility, 4),
        "serendipity_score": round(serendipity_score, 4),
        "structural_alignment": alignment,
        "narrative_clarity": clarity,
        "information_integrity": integrity,
        "reasoning": eval_data.get("reasoning", ""),
        "is_valid": is_valid
    }
