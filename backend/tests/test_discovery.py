import pytest
from app.discovery import generate_disruption_map, select_far_band_candidate

def test_generate_disruption_map():
    # Test using mock mode (no GROQ_API_KEY configured)
    known_topic = "Baking bread"
    res = generate_disruption_map(known_topic)
    
    assert "near_band" in res
    assert "mid_band" in res
    assert "far_band" in res
    assert len(res["far_band"]) > 0
    
    candidate = res["far_band"][0]
    assert "concept" in candidate
    assert "analogy_potential" in candidate
    assert "retained_rules" in candidate
    assert "measured_similarity" in candidate

def test_select_far_band_candidate():
    mock_map = {
        "far_band": [
            {
                "concept": "Semiconductor manufacturing",
                "measured_similarity": 0.15,
                "analogy_potential": "Step-by-step lithography aligns with layering process"
            },
            {
                "concept": "Mycorrhizal networks",
                "measured_similarity": 0.28,
                "analogy_potential": "Resource sharing maps to baking ingredient distribution"
            }
        ]
    }
    
    # Low mastery should sort candidates to prefer slightly higher similarity (0.28)
    cand_low = select_far_band_candidate(mock_map, user_mastery=1.0)
    assert cand_low["concept"] == "Mycorrhizal networks"
    
    # High mastery should sort candidates to prefer lower similarity (0.15)
    cand_high = select_far_band_candidate(mock_map, user_mastery=3.5)
    assert cand_high["concept"] == "Semiconductor manufacturing"
    
if __name__ == "__main__":
    pytest.main()
