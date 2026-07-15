import json
from typing import Dict, Any, List
from app.groq_client import groq_client

ABSTRACTOR_SYSTEM_PROMPT = """
You are "Agent A: Relational Systems Abstractor".
Your role is to analyze a raw text description of a niche, distant scientific or systemic concept and distill it into a pure relational schema.
You must ignore superficial details and extract the core logical scaffolding of how the system functions.

Output a JSON object containing:
1. "entities": List of the core functional agents or nodes in the system (what they are, abstractly).
2. "rules": List of the operational rules, mechanics, or constraints governing the system.
3. "causal_relationships": List of explicit cause-and-effect chains (If Event X occurs, it causes State Y).

Example output format:
{
  "entities": ["Producer node", "Distributor connection", "Resource token"],
  "rules": [
    "Resources flow from high-surplus nodes to high-deficit nodes.",
    "Connections levy a small energy fee to transport resources."
  ],
  "causal_relationships": [
    "If a producer is resource-depleted, the distributor routes stored tokens to it.",
    "If all nodes are in equilibrium, the network enters a low-consumption state."
  ]
}

Return ONLY a valid JSON object. Do not include markdown code fence formatting.
"""

TRANSLATOR_SYSTEM_PROMPT = """
You are "Agent B: Analogical Translation Engine".
Your role is to map an abstract relational schema of a target concept onto a user's known hobby domain, producing a blended narrative (analogy explanation).

Inputs:
- User's Known Hobby: The domain the user already understands.
- Target Topic: The distant domain.
- Target Relational Schema: The JSON schema of entities, rules, and causal relationships.

Task:
Generate an alignment that maps every abstract rule and entity from the target domain directly onto vocabulary, concepts, and actions of the user's hobby.
Produce a JSON object containing:
1. "suggested_title": A punchy, gamified title that combines both worlds (e.g., "The Flour-Sharing Fungal Network" or "Baking Lithography").
2. "explanation": A punchy, clever explanation of the target concept in terms of the user's hobby (approx 2-3 paragraphs). It must explain *how* the target concept operates using the mechanics of the hobby.
3. "vocabulary_mapping": A dictionary mapping terms from the target concept to terms in the user's hobby (e.g., {"Fungal network": "Central flour trading cabinet", "Trees": "Bakers"}).

Example output format:
{
  "suggested_title": "Bread-Baking Ecosystems: The Flour-Sharing Net",
  "explanation": "Did you know that baking bread in a community kitchen can behave exactly like an underground forest? In nature, mycorrhizal networks allow trees to swap carbon for minerals. In your baking world, this is just like when bakers swap excess flour for sugar through a shared kitchen pantry to ensure everyone can finish their loaves...",
  "vocabulary_mapping": {
    "Fungi Threads": "Kitchen Pantry",
    "Trees": "Bakers",
    "Carbon": "Flour",
    "Phosphorus": "Sugar"
  }
}

Return ONLY a valid JSON object. Do not include markdown code fence formatting.
"""

def abstract_target_concept(target_topic: str, raw_text: str) -> Dict[str, Any]:
    """
    Agent A (Abstractor): Distills raw text of the target domain into a relational schema.
    """
    prompt = f"Target Topic: {target_topic}\nRaw Text:\n{raw_text}"
    response_text = groq_client.generate(
        prompt=prompt,
        system_prompt=ABSTRACTOR_SYSTEM_PROMPT.strip(),
        temperature=0.2,
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
        return json.loads(clean_text)
    except Exception as e:
        print(f"Failed to parse Abstractor JSON output: {e}. Raw text:\n{response_text}")
        return {
            "entities": ["Primary node", "Secondary node", "Resource"],
            "rules": ["Resources are shared based on demand"],
            "causal_relationships": ["If a node has low resources, it requests more"]
        }

def translate_schema_to_hobby(known_hobby: str, target_topic: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent B (Translator): Maps target schema onto the user's known hobby vocabulary.
    """
    prompt = (
        f"User's Known Hobby: {known_hobby}\n"
        f"Target Topic: {target_topic}\n"
        f"Target Relational Schema: {json.dumps(schema, indent=2)}"
    )
    response_text = groq_client.generate(
        prompt=prompt,
        system_prompt=TRANSLATOR_SYSTEM_PROMPT.strip(),
        temperature=0.3,
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
        return json.loads(clean_text)
    except Exception as e:
        print(f"Failed to parse Translator JSON output: {e}. Raw text:\n{response_text}")
        return {
            "suggested_title": f"{known_hobby} meets {target_topic}",
            "explanation": f"This blends {known_hobby} and {target_topic} together. The entities of {target_topic} behave like your hobby objects.",
            "vocabulary_mapping": {target_topic: known_hobby}
        }
