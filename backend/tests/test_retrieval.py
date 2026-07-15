import pytest
from app.retrieval import retrieve_target_knowledge

def test_retrieve_target_knowledge_fallback():
    # Test retrieving a topic with no internet or API failure fallback
    res = retrieve_target_knowledge("mycorrhizal networks")
    assert "Mycorrhizal networks" in res or "fungi" in res or "underground" in res
    
    res_generic = retrieve_target_knowledge("Some super niche random concept 12345")
    assert "Some super niche random concept 12345" in res_generic or "structured system" in res_generic

if __name__ == "__main__":
    pytest.main()
