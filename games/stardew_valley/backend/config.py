import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the backend directory or project root
backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env")

def _get_env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    APP_PORT: int = _get_env_int("APP_PORT", 8000)
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    ENABLE_LLM: bool = os.getenv("ENABLE_LLM", "true").lower() in ("true", "1", "yes")
    HTTP_TIMEOUT_SECONDS: float = _get_env_float("HTTP_TIMEOUT_SECONDS", 5.0)

settings = Settings()
