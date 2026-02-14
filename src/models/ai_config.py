"""Centralized AI Model Configuration.

This module provides a single source of truth for all AI model settings.
It reads from ai_config.properties and provides type-safe access to model
configuration for all agents.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Literal, Optional

from dotenv import load_dotenv

# Load .env first (for backward compatibility)
load_dotenv()


@dataclass
class ModelConfig:
    """Configuration for a specific model/provider."""

    provider: Literal["ollama", "openrouter"]
    model: str
    temperature: float
    max_tokens: int
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    fallback_model: Optional[str] = None


class AIModelConfiguration:
    """Centralized AI model configuration manager.

    This class reads from ai_config.properties and provides typed access
    to model settings. It supports:
    - Multiple providers (ollama, openrouter)
    - Agent-specific overrides
    - Fallback to environment variables
    - Hot-reloading from file
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration from properties file.

        Args:
            config_path: Path to ai_config.properties. If None, looks in project root.
        """
        if config_path is None:
            # Look for ai_config.properties in project root
            config_path = Path.cwd() / "ai_config.properties"
            # Fallback to script directory if not found
            if not config_path.exists():
                config_path = (
                    Path(__file__).parent.parent.parent / "ai_config.properties"
                )

        self.config_path = config_path
        self._props: Dict[str, str] = {}
        self._load_properties()

    def _load_properties(self) -> None:
        """Load properties from file."""
        if not self.config_path.exists():
            # Use defaults
            self._props = {}
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Parse key=value
                if "=" in line:
                    key, value = line.split("=", 1)
                    self._props[key.strip()] = value.strip()

    def _get(self, key: str, default: str = "") -> str:
        """Get property value with environment variable fallback."""
        # Try properties file first
        if key in self._props:
            return self._props[key]
        # Fall back to environment variable (uppercase, dots to underscores)
        env_key = key.upper().replace(".", "_")
        return os.getenv(env_key, default)

    def _get_float(self, key: str, default: float) -> float:
        """Get float property."""
        value = self._get(key)
        if value:
            try:
                return float(value)
            except ValueError:
                pass
        return default

    def _get_int(self, key: str, default: int) -> int:
        """Get int property."""
        value = self._get(key)
        if value:
            try:
                return int(value)
            except ValueError:
                pass
        return default

    def get_provider(self) -> Literal["ollama", "openrouter"]:
        """Get the selected AI provider."""
        provider = self._get("ai.provider", "ollama")
        if provider not in ("ollama", "openrouter"):
            return "ollama"
        return provider  # type: ignore

    def get_model_config(self, agent_name: Optional[str] = None) -> ModelConfig:
        """Get model configuration for a specific agent.

        Args:
            agent_name: Name of the agent (e.g., "brainstorm", "content").
                       If None, returns default configuration.

        Returns:
            ModelConfig with provider, model name, temperature, etc.
        """
        provider = self.get_provider()

        # Handle Ollama configuration
        if provider == "ollama":
            config = ModelConfig(
                provider="ollama",
                model=self._get("ollama.model", "gpt-oss:20b-cloud"),
                temperature=self._get_float("ollama.temperature", 0.7),
                max_tokens=self._get_int("ollama.max_tokens", 2048),
                base_url=self._get("ollama.base_url", "http://localhost:11434/v1"),
                fallback_model=self._get("ollama.fallback_model", "qwen:1.7b"),
            )
        else:  # openrouter
            config = ModelConfig(
                provider="openrouter",
                model=self._get("openrouter.model", "google/gemma-2-9b-it:free"),
                temperature=self._get_float("openrouter.temperature", 0.7),
                max_tokens=self._get_int("openrouter.max_tokens", 2048),
                base_url=self._get(
                    "openrouter.base_url", "https://openrouter.ai/api/v1"
                ),
                api_key=self._get("openrouter.api_key", ""),
            )

        # Apply agent-specific overrides if provided
        if agent_name:
            # Check for agent-specific model override
            agent_model = self._get(f"agent.{agent_name}.model")
            if agent_model:
                config.model = agent_model

            # Check for agent-specific temperature
            agent_temp_str = self._get(f"agent.{agent_name}.temperature")
            if agent_temp_str:
                try:
                    config.temperature = float(agent_temp_str)
                except ValueError:
                    pass

            # Check for agent-specific max_tokens
            agent_tokens_str = self._get(f"agent.{agent_name}.max_tokens")
            if agent_tokens_str:
                try:
                    config.max_tokens = int(agent_tokens_str)
                except ValueError:
                    pass

        return config

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_properties()


# Global singleton instance
_config_instance: Optional[AIModelConfiguration] = None


def get_ai_config() -> AIModelConfiguration:
    """Get the global AIModelConfiguration instance.

    Returns:
        Singleton AIModelConfiguration instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AIModelConfiguration()
    return _config_instance


def reload_ai_config() -> None:
    """Reload the global configuration from file.

    Useful for tests or hot-reloading.
    """
    global _config_instance
    if _config_instance is not None:
        _config_instance.reload()
    else:
        _config_instance = AIModelConfiguration()
