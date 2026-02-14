"""Configuration management for the PPTX agent.

This module reads environment variables from a `.env` file (if present) and
exposes a simple `get_config()` function that returns a dictionary of
configuration parameters used throughout the system.  Defaults are provided
to ensure the application operates in offline mode without requiring user
input.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration values loaded from the environment.

    Attributes:
        mode: Operation mode (`offline` or `online`).  Offline mode disables
            external network calls.
        db_path: Path to the SQLite database file used for checkpointing.
        ollama_base: Base URL for the Ollama API.  Only used in offline mode
            if an Ollama server is running locally.
        openrouter_base: Base URL for the OpenRouter API (online mode).
        openrouter_api_key: API key for OpenRouter.  Required only when
            `mode=online`.
    """

    mode: str = "offline"
    checkpoint_backend: str = "sqlite"
    db_path: str = "checkpoints.db"
    postgres_url: Optional[str] = None
    redis_url: Optional[str] = None
    ollama_base: str = "http://localhost:11434/v1"
    openrouter_base: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables, with defaults.

        The `.env` file is loaded automatically via python‑dotenv if present.
        """
        load_dotenv()
        return cls(
            mode=os.getenv("MODE", "offline"),
            checkpoint_backend=os.getenv("CHECKPOINT_BACKEND", "sqlite"),
            db_path=os.getenv("DB_PATH", "checkpoints.db"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL"),
            ollama_base=os.getenv("OLLAMA_BASE", "http://localhost:11434/v1"),
            openrouter_base=os.getenv(
                "OPENROUTER_BASE", "https://openrouter.ai/api/v1"
            ),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        )


def get_config() -> Config:
    """Return a cached Config instance.

    Lazily load the configuration so tests can override environment variables
    before calling this function.
    """
    return Config.from_env()
