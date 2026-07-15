import pytest
from app.sme import abstract_target_concept, translate_schema_to_hobby

def test_abstract_target_concept():
    # Test using mock fallback
    target_topic = "Mycorrhizal networks"
    raw_text = "Fungi connect roots of different trees to share carbon and warning signals."
    schema = abstract_target_concept(target_topic, raw_text)
    
    assert "entities" in schema
    assert "rules" in schema
    assert "causal_relationships" in schema
    assert len(schema["entities"]) > 0

def test_translate_schema_to_hobby():
    # Test translation using mock data
    known_hobby = "Baking bread"
    target_topic = "Mycorrhizal networks"
    schema = {
        "entities": ["Fungi threads", "Trees", "Carbon", "Nutrients"],
        "rules": ["Carbon is exchanged for minerals"],
        "causal_relationships": ["If a tree is shaded, network routes resources"]
    }
    
    translation = translate_schema_to_hobby(known_hobby, target_topic, schema)
    
    assert "suggested_title" in translation
    assert "explanation" in translation
    assert "vocabulary_mapping" in translation

if __name__ == "__main__":
    pytest.main()
