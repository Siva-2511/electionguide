"""
config.py

Centralized configuration module for the application.
Ensures environment variables are fetched predictably and safely,
with sensible defaults.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file before reading them
load_dotenv()


class Config:
    """Application configuration settings."""

    # Environment
    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT: int = int(os.getenv("PORT", 5000))
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "fallback-dev-secret-key")

    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GOOGLE_CIVIC_API_KEY: Optional[str] = os.getenv("GOOGLE_CIVIC_API_KEY")

    # OAuth
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    @classmethod
    def is_development(cls) -> bool:
        """Check if the app is running in development mode."""
        return cls.FLASK_ENV == "development"
