import pytest
from app.evaluator import evaluate_serendipity

def test_evaluate_serendipity():
    known_hobby = "Baking bread"
    target_topic = "Mycorrhizal networks"
    schema = {
        "entities": ["Fungi threads", "Trees", "Carbon", "Nutrients"],
        "rules": ["Carbon is exchanged for minerals"],
        "causal_relationships": ["If a tree is shaded, network routes resources"]
    }
    translation = {
        "suggested_title": "Bread-Baking Ecosystems: The Flour-Sharing Net",
        "explanation": "Did you know that baking bread in a community kitchen can behave exactly like an underground forest...",
        "vocabulary_mapping": {
            "Fungi Threads": "Kitchen Pantry",
            "Trees": "Bakers"
        }
    }
    
    res = evaluate_serendipity(known_hobby, target_topic, schema, translation)
    
    assert "unexpectedness" in res
    assert "utility" in res
    assert "serendipity_score" in res
    assert "is_valid" in res
    assert res["unexpectedness"] >= 0.0
    assert res["utility"] >= 0.0

if __name__ == "__main__":
    pytest.main()
