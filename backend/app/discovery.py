import json
from typing import Dict, List, Any
from app.groq_client import groq_client
from app.embeddings import get_similarity

DISCOVERY_SYSTEM_PROMPT = """
You are a "Semantic Disrupter" in a structure-mapping recommender system.
Your goal is to break the user's filter bubble by finding extremely distant, obscure topics (far band) that share deep, non-obvious structural analogies with a topic they already understand.

Given a known topic, output a JSON object containing:
1. "near_band": 3 topics closely related to the known topic (high surface similarity, same domain).
2. "mid_band": 3 topics moderately related (different domain, but shared concepts/jargon).
3. "far_band": 3 topics extremely far (completely different domain, zero surface similarity, obscure/academic/niche) that STILL have a strong structural analogy or relational schema matching the known topic.

For each concept in the "far_band", you must provide:
- "concept": Name of the distant concept.
- "branch_from": The sub-aspect or concept of the known topic it branched from.
- "distance_heuristic": Description of why it is semantically far (different vocabulary, scales, or fields).
- "analogy_potential": A description of the structural analogy (how relations/rules in the known topic map onto it).
- "retained_rules": A list of 1-2 core relational rules or causal mechanics shared between both domains.

Example response format:
{
  "near_band": ["Chess open theory", "Checkers", "Go"],
  "mid_band": ["Game theory", "Military strategy", "Pathfinding algorithms"],
  "far_band": [
    {
      "concept": "Mycorrhizal networks",
      "branch_from": "Chess board piece coordination and resource control",
      "distance_heuristic": "Shifts from human board games to subterranean symbiotic biology, utilizing completely different entities (fungi, roots) and jargon.",
      "analogy_potential": "Both Chess and Mycorrhizal networks involve distributed nodes (pieces/trees) coordinating across a grid (board/soil) to manage and exchange resources (squares/nutrients) for mutual preservation.",
      "retained_rules": ["Strategic trade of assets to stabilize vulnerable areas", "Coordinated communication pathways to defend against threats"]
    }
  ]
}

Return ONLY a valid JSON object. Do not include markdown code fence formatting like ```json or any other text before/after.
"""

def generate_disruption_map(known_topic: str) -> Dict[str, Any]:
    """
    Generates near/mid/far concept bands from the known topic using the Groq LLM.
    """
    prompt = f"Known Topic: {known_topic}"
    response_text = groq_client.generate(
        prompt=prompt,
        system_prompt=DISCOVERY_SYSTEM_PROMPT.strip(),
        temperature=0.4,
        response_format="json"
    )
    
    # Strip markdown if LLM returned it anyway
    clean_text = response_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text.replace("```json", "", 1)
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    try:
        data = json.loads(clean_text)
    except Exception as e:
        print(f"Failed to parse JSON discovery output: {e}. Raw text:\n{response_text}")
        # Return fallback structured data
        data = {
            "near_band": [f"{known_topic} history", f"Basic {known_topic}", f"Advanced {known_topic}"],
            "mid_band": [f"Systems of {known_topic}", f"Dynamics of {known_topic}"],
            "far_band": [
                {
                    "concept": "Mycorrhizal networks",
                    "branch_from": "resource distribution",
                    "distance_heuristic": "Ecological biology vs user hobby",
                    "analogy_potential": "Resource exchange for stability",
                    "retained_rules": ["Resources are shared to balance weak nodes"]
                }
            ]
        }
    
    # Verify semantic distance using local embeddings
    # Compute similarity between known topic and each far candidate
    for item in data.get("far_band", []):
        cand = item.get("concept", "")
        similarity = get_similarity(known_topic, cand)
        item["measured_similarity"] = round(similarity, 4)
        
        # Categorize based on similarity
        if similarity > 0.6:
            item["distance_band"] = "near"
        elif similarity >= 0.3:
            item["distance_band"] = "mid"
        else:
            item["distance_band"] = "far"
            
    return data

def select_far_band_candidate(discovery_map: Dict[str, Any], user_mastery: float = 1.0) -> Dict[str, Any]:
    """
    Selects the most suitable far-band candidate based on the user's mastery level.
    Higher mastery level prefers lower similarity (further semantic distance) candidates.
    """
    candidates = discovery_map.get("far_band", [])
    if not candidates:
        raise ValueError("No far band candidates found.")
    
    # Sort candidates: we want low similarity (unexpected) but with strong analogy
    # If mastery is high, we sort strictly by lowest similarity.
    # If mastery is low, we sort by moderate similarity to ease them in, or just pick the best analogical potential.
    if user_mastery > 2.0:
        # High mastery: prefer lowest similarity
        candidates.sort(key=lambda x: x.get("measured_similarity", 0.5))
    else:
        # Low/medium mastery: prefer candidates with slightly higher similarity or the first default
        candidates.sort(key=lambda x: x.get("measured_similarity", 0.5), reverse=True)
        
    selected = candidates[0]
    
    # Log details
    print(f"Discovery selected candidate: {selected['concept']}")
    print(f"Branched from: {selected.get('branch_from')}")
    print(f"Measured Similarity: {selected.get('measured_similarity')}")
    
    return selected
