import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


class Settings:
    def __init__(self) -> None:
        self.mongo_url = os.getenv("MONGO_URL", "").strip()
        self.db_name = os.getenv("DB_NAME", "").strip()
        self.secret_key = os.getenv("SECRET_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.ai_fallback_mode = os.getenv("AI_FALLBACK_MODE", "auto").strip().lower()

        cors_origins = os.getenv("CORS_ORIGINS", "")
        self.cors_origins = [
            origin.strip()
            for origin in cors_origins.split(",")
            if origin.strip()
        ] or list(DEFAULT_CORS_ORIGINS)

        self._validate_core_settings()

    def _validate_core_settings(self) -> None:
        missing = []

        if not self.mongo_url:
            missing.append("MONGO_URL")
        if not self.db_name:
            missing.append("DB_NAME")
        if not self.secret_key:
            missing.append("SECRET_KEY")

        if missing:
            missing_values = ", ".join(missing)
            raise RuntimeError(
                f"Missing required backend environment variables: {missing_values}"
            )

    def require_gemini(self) -> None:
        if not self.gemini_api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Add it to backend/.env before using AI routes."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
