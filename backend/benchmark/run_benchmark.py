import os
import sys
import time
import argparse
import random
import json
import sqlite3
import pandas as pd
import numpy as np

# Ensure backend folder is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db import db_manager
from app.instrumentation import DB_PATH, CSV_PATH

client = TestClient(app)

# The 8 default hobby categories requested
HOBBIES = [
    "Cooking",
    "Art",
    "Sports",
    "Coding",
    "Music",
    "Photography",
    "Gardening",
    "Writing"
]

def run_pipeline(hobby: str, distance_band: str = "far", prompt_variant: str = "original", bypass_cache: bool = False) -> dict:
    """Invokes the FastAPI pipeline locally via TestClient and intercepts the metric logging."""
    # If cache is bypassed, we temporarily disable cache reads by monkey-patching
    from app.db import DatabaseManager
    original_get_llm = DatabaseManager.get_llm_cache
    original_get_http = DatabaseManager.get_http_cache

    if bypass_cache:
        DatabaseManager.get_llm_cache = lambda *args, **kwargs: None
        DatabaseManager.get_http_cache = lambda *args, **kwargs: None

    payload = {
        "user_id": "benchmark_user",
        "known_topic": hobby,
        "distance_band": distance_band,
        "prompt_variant": prompt_variant
    }

    try:
        response = client.post("/api/generate", json=payload)
        if response.status_code != 200:
            print(f"Error running pipeline for {hobby}: {response.text}")
            return {}
        
        data = response.json()
        
        # Simulate a user answering the challenge to execute Layer 6 (Rubric Grader)
        challenge = data["challenge"]
        challenge["hobby"] = hobby
        challenge["target_topic"] = data["target_topic"]
        challenge["difficulty"] = data["user_state"]["mastery"]
        challenge["prompt_variant"] = prompt_variant
        
        # Simulate standard responses (varying quality for grading representation)
        answers = [
            "I would apply this rule directly to coordinate shared ovens and swap ingredients dynamically based on bakers' needs to optimize overall kitchen throughput.",
            "I'm not sure, maybe I'll just trade items with my friends whenever someone asks for it.",
            "This concept doesn't apply to my hobby because baking bread is a purely individual process and doesn't require coordination of resources."
        ]
        chosen_answer = random.choice(answers)
        
        submit_payload = {
            "user_id": "benchmark_user",
            "challenge": challenge,
            "user_answer": chosen_answer
        }
        
        submit_response = client.post("/api/submit-challenge", json=submit_payload)
        
        return {
            "generate": data,
            "submit": submit_response.json() if submit_response.status_code == 200 else {}
        }
    finally:
        # Restore cache methods
        DatabaseManager.get_llm_cache = original_get_llm
        DatabaseManager.get_http_cache = original_get_http

def run_experiment_1():
    """Experiment 1: Semantic Distance Thresholds (Near vs Mid vs Far)"""
    print("\n--- Running Experiment 1: Distance Thresholds ---")
    hobbies_to_test = HOBBIES[:3] # Use subset to avoid rate limit spam if run in live
    results = []
    
    for hobby in hobbies_to_test:
        for band in ["near", "mid", "far"]:
            print(f"Running hobby: {hobby} | Band: {band}")
            run_pipeline(hobby, distance_band=band)
            # Sleep to avoid rate limits if live
            time.sleep(1.5)

def run_experiment_2(mock_mode: bool):
    """Experiment 2: Caching (Enabled vs Disabled)"""
    print("\n--- Running Experiment 2: Caching (Enabled vs Disabled) ---")
    hobby = "Cooking"
    
    # Run 1: Cache Disabled
    print("Running with Cache Disabled...")
    run_pipeline(hobby, bypass_cache=True)
    
    # Run 2: Cache Enabled (First time, potential miss/hit)
    print("Running with Cache Enabled (Initial)...")
    run_pipeline(hobby, bypass_cache=False)
    
    # Run 3: Cache Enabled (Guaranteed hit if not mock or cached)
    print("Running with Cache Enabled (Repeat)...")
    run_pipeline(hobby, bypass_cache=False)

def run_experiment_3():
    """Experiment 3: Prompt Variants (Original vs Variant A vs Variant B)"""
    print("\n--- Running Experiment 3: Prompt Variants ---")
    hobbies_to_test = HOBBIES[:3]
    for hobby in hobbies_to_test:
        for variant in ["original", "variant_a", "variant_b"]:
            print(f"Running hobby: {hobby} | Variant: {variant}")
            run_pipeline(hobby, prompt_variant=variant)
            time.sleep(1.5)

def run_experiment_4():
    """Experiment 4: Different Hobby Categories"""
    print("\n--- Running Experiment 4: Hobby Categories ---")
    for hobby in HOBBIES:
        print(f"Running hobby category: {hobby}")
        run_pipeline(hobby)
        time.sleep(1.5)

def run_experiment_5(runs_count: int = 10):
    """Experiment 5: Multiple Runs (Consistency Check)"""
    print(f"\n--- Running Experiment 5: Multiple Runs ({runs_count} runs per category) ---")
    # For every category, run it N times
    # With caching enabled, repeat runs are instantaneous and capture cache efficiency
    for hobby in HOBBIES:
        print(f"Running consistency check for: {hobby} ({runs_count} iterations)...")
        for i in range(runs_count):
            run_pipeline(hobby)
            if i % 3 == 0:
                time.sleep(1.0)

def main():
    parser = argparse.ArgumentParser(description="Zero-Shot Cognitive Cross-Pollination Benchmark Runner")
    parser.add_argument("--mock", action="store_true", help="Force mock API response mode (recommended for offline checks)")
    parser.add_argument("--runs", type=int, default=10, help="Number of runs for consistency check (Experiment 5)")
    args = parser.parse_args()

    # If --mock is forced, override settings/groq API settings to activate mock responses
    if args.mock:
        settings.groq_api_key = "gsk_mock_key"
        from app.groq_client import groq_client
        groq_client.client = None
        print("FORCING OFFLINE MOCK MODE. No network API calls will be made.")

    start_time = time.time()
    
    # Run all benchmarking experiments
    run_experiment_1()
    run_experiment_2(args.mock)
    run_experiment_3()
    run_experiment_4()
    run_experiment_5(args.runs)
    
    duration = time.time() - start_time
    print(f"\n✅ All Benchmark Experiments completed in {duration:.2f} seconds!")
    print(f"Metrics saved to:\n - SQLite Database: {DB_PATH}\n - CSV file: {CSV_PATH}")

    # Automatically call the plotting utility to generate figures
    print("\n📊 Generating research visualizations...")
    try:
        from benchmark.generate_plots import generate_all_plots
        generate_all_plots()
        print("Visualizations successfully saved to: backend/benchmark/figures/")
    except Exception as e:
        print(f"Error generating plots: {e}")

if __name__ == "__main__":
    main()
