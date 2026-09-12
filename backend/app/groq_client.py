import time
import random
import json
from typing import Dict, Any, Optional, List
from groq import Groq, RateLimitError
from app.config import settings
from app.db import db_manager

class GroqClientWrapper:
    def __init__(self):
        # We allow running in "offline/mock" mode if GROQ_API_KEY is not provided,
        # so the application can be explored or tested without keys if needed.
        self.api_key = settings.groq_api_key
        if self.api_key and not self.api_key.startswith("gsk_your_key_here"):
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            print("WARNING: GROQ_API_KEY not set. Operating in MOCK mode.")

        # Models list, in order of preference
        candidate_models = [
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3.6-27b",
            "openai/gpt-oss-120b",
            "gemma2-9b-it"
        ]
        if getattr(settings, "groq_model", ""):
            candidate_models.insert(0, settings.groq_model)

        self.models = candidate_models
        if self.client:
            try:
                available = {m.id for m in self.client.models.list().data}
                matched = [m for m in candidate_models if m in available]
                if matched:
                    self.models = matched
                else:
                    chat_candidates = [m for m in available if not m.startswith("whisper") and "guard" not in m]
                    if chat_candidates:
                        self.models = sorted(chat_candidates)
                print(f"Active Groq models detected: {self.models}")
            except Exception as e:
                print(f"Notice: Could not query available Groq models ({e}), using candidate list.")

    def _get_mock_response(self, prompt: str, system_prompt: str = "") -> str:
        """Returns a generic mock response when API key is missing."""
        sys_lower = system_prompt.lower()
        prompt_lower = prompt.lower()
        
        # 1. Match based on explicit agent role in the system prompt (most reliable)
        if "disrupter" in sys_lower:
            return json.dumps({
                "near_band": ["Hobby mechanics", "Rules of play", "Hobby strategies"],
                "mid_band": ["Analogous field", "Applied designs", "Related industries"],
                "far_band": [
                    {
                        "concept": "Mycorrhizal networks",
                        "branch_from": "Hobby resource sharing",
                        "distance_heuristic": "Distant biological system vs user hobby",
                        "analogy_potential": "Excellent structural analogy with resources, nodes, signals, and dynamic trading.",
                        "retained_rules": ["Strategic trade of assets to stabilize vulnerable areas"]
                    }
                ]
            })
        elif "abstractor" in sys_lower:
            return json.dumps({
                "entities": ["Fungal threads", "Tree roots", "Carbon", "Nutrients"],
                "rules": [
                    "Carbon is exchanged for minerals based on mutual availability.",
                    "Struggling nodes receive subsidization from thriving nodes."
                ],
                "causal_relationships": [
                    "If a tree has excess sugar, it routes it to the fungal network.",
                    "If a node is shaded/weak, the network sends extra phosphorus to support it."
                ]
            })
        elif "translation engine" in sys_lower:
            return json.dumps({
                "suggested_title": "Bread-Baking Ecosystems: The Flour-Sharing Net",
                "explanation": "Did you know that baking bread in a community kitchen can behave exactly like an underground forest? In nature, mycorrhizal networks allow trees to swap carbon for minerals. In your baking world, this is just like when bakers swap excess flour for sugar through a shared kitchen pantry to ensure everyone can finish their loaves...",
                "vocabulary_mapping": {
                  "Fungi Threads": "Kitchen Pantry",
                  "Trees": "Bakers",
                  "Carbon": "Flour",
                  "Phosphorus": "Sugar"
                }
            })
        elif "utility evaluator" in sys_lower:
            return json.dumps({
                "structural_alignment_score": 0.9,
                "narrative_clarity_score": 0.85,
                "information_integrity_score": 0.95,
                "reasoning": "The target domain is highly distant, yet the trade analogy is incredibly strong and clean."
            })
        elif "challenge generator" in sys_lower:
            return json.dumps({
                "scenario": "Your baking club has 5 bakers. 2 bakers have excess flour but no sugar. 3 bakers have excess sugar but no flour.",
                "question": "Using the resource-trading logic of mycorrhizal networks, how do you structure your baking club's sharing system?",
                "required_rule_to_apply": "Carbon is traded for phosphorus based on mutual surplus/need.",
                "hint": "Think about how trees swap what they have too much of to ensure the entire forest survives."
            })
        elif "analogy grader" in sys_lower:
            return json.dumps({
                "rubric_checks": {
                    "rule_application": {
                        "score": 3,
                        "max_score": 3,
                        "justification": "Correctly implemented mutual trade of surplus resources to keep weak nodes alive."
                    },
                    "contextual_coherence": {
                        "score": 3,
                        "max_score": 3,
                        "justification": "The explanation makes total sense within the hobby context."
                    },
                    "analogical_understanding": {
                        "score": 3,
                        "max_score": 3,
                        "justification": "Demonstrated solid understanding of mycorrhizal resource balancing."
                    }
                },
                "feedback": "Perfect response! You successfully applied the ecological resource sharing rules to resolve the hobby supply shortage."
            })

        # 2. Fallback to prompt-based matching (for test cases calling generate directly)
        if "semantic distance map" in prompt_lower or "near/mid/far" in prompt_lower:
            return json.dumps({
                "near": ["Hobby mechanics", "Rules of play", "Hobby strategies"],
                "mid": ["Analogous field", "Applied designs", "Related industries"],
                "far": [
                    {
                        "concept": "Mycorrhizal networks",
                        "analogy_potential": "Excellent structural analogy with resources, nodes, signals, and dynamic trading.",
                        "reasoning": "Distant ecological system that maps directly to hobby resource sharing."
                    }
                ]
            })
        elif "translator" in prompt_lower or "blended narrative" in prompt_lower:
            return json.dumps({
                "suggested_title": "Bread-Baking Ecosystems: The Flour-Sharing Net",
                "explanation": "Did you know that baking bread in a community kitchen can behave exactly like an underground forest? In nature, mycorrhizal networks allow trees to swap carbon for minerals. In your baking world, this is just like when bakers swap excess flour for sugar through a shared kitchen pantry to ensure everyone can finish their loaves...",
                "vocabulary_mapping": {
                  "Fungi Threads": "Kitchen Pantry",
                  "Trees": "Bakers"
                }
            })
        elif "serendipity" in prompt_lower:
            return json.dumps({
                "unexpectedness": 0.85,
                "utility": 0.9,
                "score": 0.76,
                "reasoning": "The target domain is highly distant, yet the trade analogy is incredibly strong and clean."
            })
        elif "micro-challenge" in prompt_lower or "challenge" in prompt_lower:
            return json.dumps({
                "scenario": "Your baking club has 5 bakers. 2 bakers have excess flour but no sugar. 3 bakers have excess sugar but no flour.",
                "question": "Using the resource-trading logic of mycorrhizal networks, how do you structure your baking club's sharing system?",
                "required_rule_to_apply": "Carbon is traded for phosphorus based on mutual surplus/need.",
                "hint": "Think about how trees swap what they have too much of to ensure the entire forest survives."
            })
        elif "rubric" in prompt_lower or "grader" in prompt_lower:
            return json.dumps({
                "rubric_checks": {
                    "rule_application": {"score": 3, "max_score": 3, "justification": "Correctly applied rule"},
                    "contextual_coherence": {"score": 3, "max_score": 3, "justification": "Makes sense"},
                    "analogical_understanding": {"score": 3, "max_score": 3, "justification": "Solid understanding"}
                },
                "feedback": "Perfect response!"
            })
        elif "relational schema" in prompt_lower or "abstractor" in prompt_lower:
            return json.dumps({
                "entities": ["Fungal threads", "Tree roots", "Carbon", "Nutrients"],
                "rules": [
                    "Carbon is exchanged for minerals based on mutual availability.",
                    "Struggling nodes receive subsidization from thriving nodes."
                ],
                "causal_relationships": [
                    "If a tree has excess sugar, it routes it to the fungal network.",
                    "If a node is shaded/weak, the network sends extra phosphorus to support it."
                ]
            })

        return "Mock response: API key is not configured. Please supply a valid Groq API key to test full agent features."

    def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.2, response_format: Optional[str] = None) -> str:
        # Check cache first
        cache_key = f"system:{system_prompt}|user:{prompt}|temp:{temperature}|format:{response_format}"
        cached = db_manager.get_llm_cache(self.models[0], cache_key)
        if cached:
            return cached

        if not self.client:
            return self._get_mock_response(prompt, system_prompt)

        # Retry logic with exponential backoff and model fallbacks
        max_retries = 5
        base_delay = 2.0
        
        # Try models in order of preference
        for model in self.models:
            for attempt in range(max_retries):
                try:
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})

                    kwargs = {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                    }
                    if response_format == "json":
                        kwargs["response_format"] = {"type": "json_object"}

                    response = self.client.chat.completions.create(**kwargs)
                    content = response.choices[0].message.content
                    
                    if content:
                        # Save in cache
                        db_manager.set_llm_cache(model, cache_key, content)
                        return content
                    
                except RateLimitError as e:
                    # Groq free tier rate limits
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0.1, 1.0)
                    print(f"Groq Rate Limit (Model: {model}). Retrying in {wait_time:.2f}s... Error: {e}")
                    time.sleep(wait_time)
                except Exception as e:
                    err_str = str(e)
                    if "model_decommissioned" in err_str or "model_not_found" in err_str or "404" in err_str:
                        print(f"Model {model} is unavailable/decommissioned ({err_str}). Moving to next model...")
                        break
                    wait_time = base_delay * (2 ** attempt)
                    print(f"Groq error (Model: {model}, Attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                    time.sleep(wait_time)
            
            print(f"Model {model} failed or rate limited continuously. Trying fallback model...")

        raise RuntimeError("All Groq models failed or exceeded maximum rate limits.")

groq_client = GroqClientWrapper()
