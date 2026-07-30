import time
import os
import csv
import json
import sqlite3
import contextvars
from typing import Dict, Any, List, Optional
from app.config import settings

# Context variable to hold telemetry metrics for the active request scope
active_metrics = contextvars.ContextVar("active_metrics", default=None)

# Path to the database and CSV
DB_PATH = settings.database_url.replace("sqlite:///", "") if settings.database_url.startswith("sqlite:///") else settings.database_url
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "benchmark_metrics.csv")

def init_benchmark_db():
    """Initializes SQLite database tables for benchmarks and manual evaluations."""
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            # Benchmark metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hobby TEXT,
                    discovered_topic TEXT,
                    cosine_similarity REAL,
                    cosine_distance REAL,
                    serendipity_score REAL,
                    unexpectedness_score REAL,
                    analogy_utility_score REAL,
                    challenge_difficulty REAL,
                    challenge_score REAL,
                    ema_before REAL,
                    ema_after REAL,
                    cache_hit_count INTEGER DEFAULT 0,
                    cache_miss_count INTEGER DEFAULT 0,
                    api_response_time REAL,
                    total_pipeline_time REAL,
                    groq_latency REAL DEFAULT 0.0,
                    estimated_token_usage INTEGER DEFAULT 0,
                    prompt_template_used TEXT,
                    prompt_variant TEXT DEFAULT 'original',
                    timestamp REAL,
                    layer_1_time REAL DEFAULT 0.0,
                    layer_2_time REAL DEFAULT 0.0,
                    layer_3_time REAL DEFAULT 0.0,
                    layer_4_time REAL DEFAULT 0.0,
                    layer_5_time REAL DEFAULT 0.0,
                    layer_6_time REAL DEFAULT 0.0
                )
            """)
            # Manual evaluations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS manual_evaluations (
                    metric_id INTEGER PRIMARY KEY,
                    correctness INTEGER,
                    clarity INTEGER,
                    structural_consistency INTEGER,
                    overall_quality REAL,
                    notes TEXT,
                    timestamp REAL,
                    FOREIGN KEY (metric_id) REFERENCES benchmark_metrics(id)
                )
            """)
    finally:
        conn.close()

def log_metrics_to_db_and_csv(metrics: Dict[str, Any]):
    """Saves metrics dictionary to SQLite and appends to CSV."""
    # Ensure tables exist
    init_benchmark_db()

    # Calculate fields
    similarity = metrics.get("cosine_similarity", 0.0)
    metrics["cosine_distance"] = round(1.0 - similarity, 4)
    metrics["unexpectedness_score"] = metrics["cosine_distance"]
    
    # Calculate Serendipity = Unexpectedness * Utility
    utility = metrics.get("analogy_utility_score", 0.0)
    metrics["serendipity_score"] = round(metrics["unexpectedness_score"] * utility, 4)
    
    metrics["timestamp"] = time.time()

    # 1. Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    metric_id = None
    try:
        with conn:
            cursor = conn.cursor()
            keys = [
                "hobby", "discovered_topic", "cosine_similarity", "cosine_distance",
                "serendipity_score", "unexpectedness_score", "analogy_utility_score",
                "challenge_difficulty", "challenge_score", "ema_before", "ema_after",
                "cache_hit_count", "cache_miss_count", "api_response_time",
                "total_pipeline_time", "groq_latency", "estimated_token_usage",
                "prompt_template_used", "prompt_variant", "timestamp",
                "layer_1_time", "layer_2_time", "layer_3_time", "layer_4_time",
                "layer_5_time", "layer_6_time"
            ]
            columns = ", ".join(keys)
            placeholders = ", ".join(["?"] * len(keys))
            values = [metrics.get(k) for k in keys]
            
            cursor.execute(
                f"INSERT INTO benchmark_metrics ({columns}) VALUES ({placeholders})",
                values
            )
            metric_id = cursor.lastrowid
    except Exception as e:
        print(f"Error saving metric to SQLite: {e}")
    finally:
        conn.close()

    # 2. Save to CSV
    file_exists = os.path.exists(CSV_PATH)
    try:
        with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                # Write header
                writer.writerow([
                    "id", "hobby", "discovered_topic", "cosine_similarity", "cosine_distance",
                    "serendipity_score", "unexpectedness_score", "analogy_utility_score",
                    "challenge_difficulty", "challenge_score", "ema_before", "ema_after",
                    "cache_hit_count", "cache_miss_count", "api_response_time",
                    "total_pipeline_time", "groq_latency", "estimated_token_usage",
                    "prompt_template_used", "prompt_variant", "timestamp",
                    "layer_1_time", "layer_2_time", "layer_3_time", "layer_4_time",
                    "layer_5_time", "layer_6_time"
                ])
            writer.writerow([
                metric_id or "",
                metrics.get("hobby", ""),
                metrics.get("discovered_topic", ""),
                metrics.get("cosine_similarity", 0.0),
                metrics.get("cosine_distance", 0.0),
                metrics.get("serendipity_score", 0.0),
                metrics.get("unexpectedness_score", 0.0),
                metrics.get("analogy_utility_score", 0.0),
                metrics.get("challenge_difficulty", 0.0),
                metrics.get("challenge_score", 0.0),
                metrics.get("ema_before", 0.0),
                metrics.get("ema_after", 0.0),
                metrics.get("cache_hit_count", 0),
                metrics.get("cache_miss_count", 0),
                metrics.get("api_response_time", 0.0),
                metrics.get("total_pipeline_time", 0.0),
                metrics.get("groq_latency", 0.0),
                metrics.get("estimated_token_usage", 0),
                metrics.get("prompt_template_used", ""),
                metrics.get("prompt_variant", "original"),
                metrics.get("timestamp", 0.0),
                metrics.get("layer_1_time", 0.0),
                metrics.get("layer_2_time", 0.0),
                metrics.get("layer_3_time", 0.0),
                metrics.get("layer_4_time", 0.0),
                metrics.get("layer_5_time", 0.0),
                metrics.get("layer_6_time", 0.0)
            ])
    except Exception as e:
        print(f"Error saving metric to CSV: {e}")

    return metric_id

# --- MONKEY-PATCHING ENGINE ---

def apply_instrumentation():
    """Dynamically wraps pipeline modules to collect stats without editing their files."""
    print("Initializing metrics collection and instrumentation...")
    init_benchmark_db()

    # 1. Wrap Groq Client to capture latencies, prompt templates, and token use
    from app.groq_client import groq_client
    original_generate = groq_client.generate

    def instrumented_generate(prompt: str, system_prompt: str = "", temperature: float = 0.2, response_format: Optional[str] = None) -> str:
        ctx = active_metrics.get()
        variant = ctx.get("prompt_variant", "original") if ctx is not None else "original"
        
        # Swaps prompt variants dynamically
        from app.prompt_variants import get_variant_system_prompt
        actual_system_prompt = get_variant_system_prompt(system_prompt, variant)
        
        start = time.time()
        
        # Determine if it's in the cache by checking cache directly
        # If cached, it returns immediately in original_generate, so we check cache key
        from app.db import db_manager
        cache_key = f"system:{actual_system_prompt}|user:{prompt}|temp:{temperature}|format:{response_format}"
        cached = db_manager.get_llm_cache(groq_client.models[0], cache_key)
        
        is_hit = cached is not None
        res = original_generate(prompt, actual_system_prompt, temperature, response_format)
        duration = time.time() - start

        if ctx is not None:
            if is_hit:
                ctx["cache_hit_count"] = ctx.get("cache_hit_count", 0) + 1
            else:
                ctx["cache_miss_count"] = ctx.get("cache_miss_count", 0) + 1
                ctx["groq_latency"] = ctx.get("groq_latency", 0.0) + duration

            # Heuristic token usage: 1 token ~= 4 characters
            tokens = (len(prompt) + len(actual_system_prompt) + len(res)) // 4
            ctx["estimated_token_usage"] = ctx.get("estimated_token_usage", 0) + tokens
            
            # Log prompt templates (system + user layout format)
            template_info = f"variant ({variant}) | system: {actual_system_prompt[:40]}... | user: {prompt[:40]}..."
            if not ctx.get("prompt_template_used"):
                ctx["prompt_template_used"] = template_info
            else:
                ctx["prompt_template_used"] += f" || {template_info}"

        return res

    groq_client.generate = instrumented_generate

    # 2. Wrap Cache queries to detect hit ratios
    from app.db import DatabaseManager
    original_get_http_cache = DatabaseManager.get_http_cache

    def instrumented_get_http_cache(self, api_name: str, query: str) -> Optional[str]:
        ctx = active_metrics.get()
        res = original_get_http_cache(self, api_name, query)
        if ctx is not None:
            if res is not None:
                ctx["cache_hit_count"] = ctx.get("cache_hit_count", 0) + 1
            else:
                ctx["cache_miss_count"] = ctx.get("cache_miss_count", 0) + 1
        return res

    DatabaseManager.get_http_cache = instrumented_get_http_cache

    # 3. Wrap pipeline layers to record execution time
    import app.discovery as discovery
    import app.retrieval as retrieval
    import app.sme as sme
    import app.evaluator as evaluator
    import app.challenge as challenge
    import app.scoring as scoring

    # Layer 1: Discovery
    orig_generate_disruption_map = discovery.generate_disruption_map
    def wrapped_generate_disruption_map(*args, **kwargs):
        ctx = active_metrics.get()
        start = time.time()
        res = orig_generate_disruption_map(*args, **kwargs)
        if ctx is not None:
            ctx["layer_1_time"] = round(time.time() - start, 4)
        return res
    discovery.generate_disruption_map = wrapped_generate_disruption_map

    # Layer 2: Retrieval
    orig_retrieve_target_knowledge = retrieval.retrieve_target_knowledge
    def wrapped_retrieve_target_knowledge(*args, **kwargs):
        ctx = active_metrics.get()
        start = time.time()
        res = orig_retrieve_target_knowledge(*args, **kwargs)
        if ctx is not None:
            ctx["layer_2_time"] = round(time.time() - start, 4)
        return res
    retrieval.retrieve_target_knowledge = wrapped_retrieve_target_knowledge

    # Layer 3: SME Engine
    orig_abstract = sme.abstract_target_concept
    orig_translate = sme.translate_schema_to_hobby
    
    def wrapped_abstract(*args, **kwargs):
        ctx = active_metrics.get()
        start = time.time()
        res = orig_abstract(*args, **kwargs)
        if ctx is not None:
            ctx["layer_3_time"] = ctx.get("layer_3_time", 0.0) + (time.time() - start)
        return res
    sme.abstract_target_concept = wrapped_abstract

    def wrapped_translate(*args, **kwargs):
        ctx = active_metrics.get()
        start = time.time()
        res = orig_translate(*args, **kwargs)
        if ctx is not None:
            ctx["layer_3_time"] = round(ctx.get("layer_3_time", 0.0) + (time.time() - start), 4)
        return res
    sme.translate_schema_to_hobby = wrapped_translate

    # Layer 4: Evaluator
    orig_evaluate = evaluator.evaluate_serendipity
    def wrapped_evaluate(*args, **kwargs):
        ctx = active_metrics.get()
        start = time.time()
        res = orig_evaluate(*args, **kwargs)
        if ctx is not None:
            ctx["layer_4_time"] = round(time.time() - start, 4)
            # Record evaluator ratings in context
            ctx["cosine_similarity"] = res.get("unexpectedness", 0.0) # wait, unexpectedness = 1.0 - similarity, so similarity = 1.0 - unexpectedness
            ctx["cosine_similarity"] = round(1.0 - res.get("unexpectedness", 0.0), 4)
            ctx["analogy_utility_score"] = res.get("utility", 0.0)
        return res
    evaluator.evaluate_serendipity = wrapped_evaluate

    # Layer 5: Challenge Generator
    orig_challenge = challenge.generate_challenge
    def wrapped_challenge(*args, **kwargs):
        ctx = active_metrics.get()
        start = time.time()
        res = orig_challenge(*args, **kwargs)
        if ctx is not None:
            ctx["layer_5_time"] = round(time.time() - start, 4)
        return res
    challenge.generate_challenge = wrapped_challenge

    # Layer 6: Rubric Grader
    orig_grade = scoring.grade_response
    def wrapped_grade(*args, **kwargs):
        ctx = active_metrics.get()
        start = time.time()
        res = orig_grade(*args, **kwargs)
        if ctx is not None:
            ctx["layer_6_time"] = round(time.time() - start, 4)
            ctx["challenge_score"] = res.get("total_score", 0.0)
            ctx["ema_before"] = res.get("old_mastery", 0.0)
            ctx["ema_after"] = res.get("new_mastery", 0.0)
        return res
    scoring.grade_response = wrapped_grade

print("Applying runtime monkey-patches...")
apply_instrumentation()
