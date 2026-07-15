import pytest
from app.scoring import grade_response
from app.db import db_manager

def test_grade_response():
    user_id = "test_user_123"
    
    # Initialize user state in DB first to ensure consistent test results
    db_manager.update_user_state(user_id, mastery=1.5, streak=2, xp=150)
    
    challenge = {
        "scenario": "Your baking club is short on flour...",
        "question": "How do you share?",
        "required_rule_to_apply": "Dynamic resource trade"
    }
    user_answer = "I will share my surplus flour with other bakers so everyone can make bread together."
    
    res = grade_response(user_id, challenge, user_answer)
    
    assert "rubric_checks" in res
    assert "total_score" in res
    assert "feedback" in res
    assert "new_streak" in res
    assert "new_xp" in res
    assert "new_mastery" in res
    
    # If the mock grader runs, it returns 100/100, which means streak goes to 3 and XP increases
    if res["total_score"] >= 60:
        assert res["new_streak"] == 3
        assert res["new_xp"] > 150
        assert res["new_mastery"] > 1.5

if __name__ == "__main__":
    pytest.main()
