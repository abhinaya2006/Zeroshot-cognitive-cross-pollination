import json
from typing import Dict, Any
from app.groq_client import groq_client
from app.db import db_manager

GRADER_SYSTEM_PROMPT = """
You are "Layer 6: Rubric-Based Analogy Grader".
Your role is to evaluate a user's free-text response to a micro-challenge.
You must grade the response strictly against a structural rubric, not on writing style or general vibes.

Inputs:
- Challenge Scenario: The setup of the problem.
- Challenge Question: The problem the user is trying to solve.
- Required Rule to Apply: The specific target domain rule.
- User Response: The text submitted by the user.

Evaluate the response on the following three criteria, giving a score from 0 (no attempt / incorrect) to 3 (excellent):
1. "rule_application": Did they correctly apply the required target domain rule to the hobby scenario?
2. "contextual_coherence": Is the proposed solution logical and realistic within their hobby context?
3. "analogical_understanding": Did they demonstrate that they understand the underlying structural relationship (the 'why') of the analogy?

Output a JSON object containing:
{
  "rubric_checks": {
    "rule_application": {
      "score": 3,
      "max_score": 3,
      "justification": "Why this score was given..."
    },
    "contextual_coherence": {
      "score": 2,
      "max_score": 3,
      "justification": "Why this score was given..."
    },
    "analogical_understanding": {
      "score": 3,
      "max_score": 3,
      "justification": "Why this score was given..."
    }
  },
  "feedback": "Supportive, clever, constructive feedback (Gen-Z friendly tone, encouraging but clear)."
}

Return ONLY a valid JSON object. Do not include markdown code fence formatting.
"""

def grade_response(user_id: str, challenge: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
    """
    Grades the user response using the LLM grader.
    Calculates total score out of 100, updates user mastery (EMA), streak, and XP in SQLite.
    """
    prompt = (
        f"Challenge Scenario: {challenge.get('scenario', '')}\n"
        f"Challenge Question: {challenge.get('question', '')}\n"
        f"Required Rule to Apply: {challenge.get('required_rule_to_apply', '')}\n"
        f"User Response: {user_answer}"
    )

    response_text = groq_client.generate(
        prompt=prompt,
        system_prompt=GRADER_SYSTEM_PROMPT.strip(),
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
        grader_data = json.loads(clean_text)
    except Exception as e:
        print(f"Failed to parse Grader JSON: {e}. Raw text:\n{response_text}")
        grader_data = {
            "rubric_checks": {
                "rule_application": {"score": 2, "max_score": 3, "justification": "Fallback grade."},
                "contextual_coherence": {"score": 2, "max_score": 3, "justification": "Fallback grade."},
                "analogical_understanding": {"score": 2, "max_score": 3, "justification": "Fallback grade."}
            },
            "feedback": "Great try! Keep connecting the dots."
        }

    # Calculate score out of 100
    checks = grader_data.get("rubric_checks", {})
    sum_scores = 0
    max_scores = 0
    for key, val in checks.items():
        sum_scores += val.get("score", 0)
        max_scores += val.get("max_score", 3)

    total_score = round((sum_scores / max_scores) * 100) if max_scores > 0 else 0

    # Retrieve current user state
    user_state = db_manager.get_user_state(user_id)
    old_mastery = user_state.get("mastery", 1.0)
    old_streak = user_state.get("streak", 0)
    old_xp = user_state.get("xp", 0)

    # Calculate new mastery (EMA: weight 0.2 on new performance, 0.8 on old)
    # Mastery maps from 1.0 (beginner) to 5.0 (expert)
    target_mastery = 1.0 + (total_score / 100.0) * 4.0
    new_mastery = round(0.2 * target_mastery + 0.8 * old_mastery, 2)
    new_mastery = max(1.0, min(5.0, new_mastery))

    # Update streak & XP (success threshold = 60/100)
    if total_score >= 60:
        new_streak = old_streak + 1
        xp_gained = total_score + (new_streak * 10)
        new_xp = old_xp + xp_gained
        success = True
    else:
        new_streak = 0
        new_xp = old_xp
        success = False

    # Update database
    db_manager.update_user_state(user_id, new_mastery, new_streak, new_xp)

    return {
        "rubric_checks": checks,
        "total_score": total_score,
        "feedback": grader_data.get("feedback", ""),
        "success": success,
        "old_streak": old_streak,
        "new_streak": new_streak,
        "old_xp": old_xp,
        "new_xp": new_xp,
        "old_mastery": old_mastery,
        "new_mastery": new_mastery
    }
