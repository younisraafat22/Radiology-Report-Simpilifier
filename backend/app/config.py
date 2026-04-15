import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    api_title: str = os.getenv("API_TITLE", "Radiology Report Simplifier API")
    max_report_chars: int = int(os.getenv("MAX_REPORT_CHARS", "6000"))
    cors_allow_origins: str = os.getenv("CORS_ALLOW_ORIGINS", "*")


settings = Settings()
