import sqlite3
import hashlib
import json
import os
import time
from typing import Optional, Dict, Any
from app.config import settings

class DatabaseManager:
    def __init__(self, db_path: str):
        # Convert sqlite:///./db.db style path to normal filepath
        clean_path = db_path
        if db_path.startswith("sqlite:///"):
            clean_path = db_path.replace("sqlite:///", "")
        
        # Ensure parent folder exists
        parent_dir = os.path.dirname(os.path.abspath(clean_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        self.db_path = clean_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            # HTTP Response Cache
            conn.execute("""
                CREATE TABLE IF NOT EXISTS http_cache (
                    api_name TEXT,
                    query TEXT,
                    response_text TEXT,
                    timestamp REAL,
                    PRIMARY KEY (api_name, query)
                )
            """)
            
            # LLM Prompt Cache
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    prompt_hash TEXT PRIMARY KEY,
                    prompt TEXT,
                    response_text TEXT,
                    model_name TEXT,
                    timestamp REAL
                )
            """)
            
            # User State (streaks, xp, difficulty/mastery score)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id TEXT PRIMARY KEY,
                    mastery REAL DEFAULT 1.0,
                    streak INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    last_active REAL
                )
            """)
            
            # Application History
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    known_topic TEXT,
                    target_topic TEXT,
                    similarity REAL,
                    explanation TEXT,
                    challenge TEXT,
                    answer TEXT,
                    score REAL,
                    evaluation TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()

    # --- HTTP Caching ---
    def get_http_cache(self, api_name: str, query: str) -> Optional[str]:
        try:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT response_text FROM http_cache WHERE api_name = ? AND query = ?",
                    (api_name.lower(), query.strip().lower())
                ).fetchone()
                return row["response_text"] if row else None
        except Exception:
            return None

    def set_http_cache(self, api_name: str, query: str, response_text: str):
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO http_cache (api_name, query, response_text, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (api_name.lower(), query.strip().lower(), response_text, time.time())
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving HTTP cache: {e}")

    # --- LLM Caching ---
    def _hash_prompt(self, model_name: str, prompt: str) -> str:
        payload = f"{model_name}:{prompt}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get_llm_cache(self, model_name: str, prompt: str) -> Optional[str]:
        prompt_hash = self._hash_prompt(model_name, prompt)
        try:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT response_text FROM llm_cache WHERE prompt_hash = ?",
                    (prompt_hash,)
                ).fetchone()
                return row["response_text"] if row else None
        except Exception:
            return None

    def set_llm_cache(self, model_name: str, prompt: str, response_text: str):
        prompt_hash = self._hash_prompt(model_name, prompt)
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO llm_cache (prompt_hash, prompt, response_text, model_name, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (prompt_hash, prompt, response_text, model_name, time.time())
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving LLM cache: {e}")

    # --- User State ---
    def get_user_state(self, user_id: str) -> Dict[str, Any]:
        try:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT mastery, streak, xp, last_active FROM user_state WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                if row:
                    return dict(row)
                else:
                    # Insert default state
                    default_state = {"mastery": 1.0, "streak": 0, "xp": 0, "last_active": time.time()}
                    conn.execute(
                        """
                        INSERT INTO user_state (user_id, mastery, streak, xp, last_active)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (user_id, default_state["mastery"], default_state["streak"], default_state["xp"], default_state["last_active"])
                    )
                    conn.commit()
                    return default_state
        except Exception as e:
            print(f"Error getting user state: {e}")
            return {"mastery": 1.0, "streak": 0, "xp": 0, "last_active": time.time()}

    def update_user_state(self, user_id: str, mastery: float, streak: int, xp: int):
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_state (user_id, mastery, streak, xp, last_active)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, mastery, streak, xp, time.time())
                )
                conn.commit()
        except Exception as e:
            print(f"Error updating user state: {e}")

    # --- History Logging ---
    def save_history(self, user_id: str, known_topic: str, target_topic: str, similarity: float,
                     explanation: str, challenge: str, answer: str, score: float, evaluation: str):
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO history (user_id, known_topic, target_topic, similarity, explanation, challenge, answer, score, evaluation, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, known_topic, target_topic, similarity, explanation, challenge, answer, score, evaluation, time.time())
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving history: {e}")

db_manager = DatabaseManager(settings.database_url)
