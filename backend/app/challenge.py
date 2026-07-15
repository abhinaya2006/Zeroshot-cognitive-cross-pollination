import json
from typing import Dict, Any
from app.groq_client import groq_client

CHALLENGE_SYSTEM_PROMPT = """
You are "Layer 5: Micro-Challenge Generator".
Your role is to build an interactive, personalized micro-challenge (like a mini-game or scenario) based on the user's hobby.
This challenge must be a concrete real-world problem in the user's hobby that can ONLY be solved correctly by applying a rule/mechanic from the new, obscure target domain.

Inputs:
- User's Known Hobby: The base domain.
- Target Topic: The distant domain.
- Target Relational Schema: The abstract rules and causal relationships.

Task:
Generate a JSON object containing:
1. "scenario": A short, engaging story/problem set in the user's hobby context (e.g., "Your community baking kitchen has a shortage of yeast, but a surplus of ovens...").
2. "question": A concrete question asking the user how they would solve this problem. Solving it must require translating the target domain's rule.
3. "required_rule_to_apply": The specific scientific/systemic rule from the Target Relational Schema that the user must adapt and apply.
4. "hint": A subtle, playful hint pointing to the analogy's mechanics (e.g., "Think about how trees balance their carbon and mineral trades!").

Example output format:
{
  "scenario": "Your baking club has 5 bakers. 2 bakers have excess flour but no sugar. 3 bakers have excess sugar but no flour. Local shops are closed.",
  "question": "Using the resource-trading logic of mycorrhizal networks, how do you structure your baking club's sharing system to maximize the total number of loaves baked?",
  "required_rule_to_apply": "Carbon is traded for phosphorus based on mutual surplus/need, prioritizing weak nodes to maintain overall network stability.",
  "hint": "Don't just run a standard shop. Think about how trees swap what they have too much of to ensure the entire forest survives."
}

Return ONLY a valid JSON object. Do not include markdown code fence formatting.
"""

def generate_challenge(known_hobby: str, target_topic: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Layer 5: Generates a micro-challenge requiring application of the target schema rule in the hobby context.
    """
    prompt = (
        f"User's Known Hobby: {known_hobby}\n"
        f"Target Topic: {target_topic}\n"
        f"Target Relational Schema: {json.dumps(schema, indent=2)}"
    )

    response_text = groq_client.generate(
        prompt=prompt,
        system_prompt=CHALLENGE_SYSTEM_PROMPT.strip(),
        temperature=0.4,
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
        print(f"Failed to parse Challenge JSON: {e}. Raw text:\n{response_text}")
        return {
            "scenario": f"You are practicing {known_hobby} and face a resource limitation.",
            "question": f"How can you apply {target_topic} resource sharing rules to solve this?",
            "required_rule_to_apply": "Share resources dynamically according to node needs.",
            "hint": "Look at the target topic mapping explanation."
        }
