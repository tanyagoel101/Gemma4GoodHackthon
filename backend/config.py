from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "VoiceTrace"
    api_prefix: str = "/api"
    database_url: str = "sqlite+aiosqlite:///./backend/voicetrace.db"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:e2b"
    ollama_fallback_model: str = "gemma3:27b"
    frontend_origin: str = "http://localhost:5173"
    whisper_model: str = "base"
    upload_dir: Path = BASE_DIR / "uploads"
    max_audio_minutes: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()

