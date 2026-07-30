import pytest
import os
import sqlite3
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from benchmark.run_benchmark import run_pipeline
from benchmark.generate_plots import generate_all_plots, FIGURES_DIR

client = TestClient(app)
DB_PATH = settings.database_url.replace("sqlite:///", "") if settings.database_url.startswith("sqlite:///") else settings.database_url

def test_benchmark_metrics_logging():
    # Force mock mode
    settings.groq_api_key = "gsk_mock_key"
    from app.groq_client import groq_client
    original_client = groq_client.client
    groq_client.client = None
    
    try:
        # Run pipeline
        res = run_pipeline("Baking bread", distance_band="far", prompt_variant="original")
        
        assert "generate" in res
        assert "submit" in res
        
        # Verify SQLite has recorded the run
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM benchmark_metrics ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        # Check column index mapping (e.g. hobby is index 1, discovered_topic is 2, etc.)
        assert "Baking bread" in row
        
    finally:
        groq_client.client = original_client

def test_generate_plots_execution():
    # Execute plot generation
    generate_all_plots()
    
    # Check that figure outputs exist
    plots = [
        "serendipity_histogram.png",
        "semantic_distance_boxplot.png",
        "analogy_quality_bar.png",
        "challenge_success_bar.png",
        "pipeline_timings_bar.png",
        "ema_progression_line.png",
        "prompt_variants_radar.png",
        "distance_vs_utility_scatter.png",
        "metrics_correlation_heatmap.png"
    ]
    
    for plot in plots:
        plot_path = os.path.join(FIGURES_DIR, plot)
        assert os.path.exists(plot_path), f"Figure not found: {plot_path}"
        # Cleanup files to keep workspace clean
        try:
            os.remove(plot_path)
        except OSError:
            pass

if __name__ == "__main__":
    pytest.main()
