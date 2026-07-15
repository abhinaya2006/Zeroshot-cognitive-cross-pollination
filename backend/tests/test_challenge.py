import pytest
from app.challenge import generate_challenge

def test_generate_challenge():
    known_hobby = "Baking bread"
    target_topic = "Mycorrhizal networks"
    schema = {
        "entities": ["Fungi threads", "Trees", "Carbon", "Nutrients"],
        "rules": ["Carbon is exchanged for minerals"],
        "causal_relationships": ["If a tree is shaded, network routes resources"]
    }
    
    challenge = generate_challenge(known_hobby, target_topic, schema)
    
    assert "scenario" in challenge
    assert "question" in challenge
    assert "required_rule_to_apply" in challenge
    assert "hint" in challenge

if __name__ == "__main__":
    pytest.main()
