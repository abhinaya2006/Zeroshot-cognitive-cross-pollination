import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str = "sqlite:///./cognitive_cross_pollination.db"
    embeddings_model: str = "all-MiniLM-L6-v2"

    # Use .env file configuration
    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
