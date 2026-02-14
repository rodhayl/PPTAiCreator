"""Model client abstractions for calling language models.

This module defines a unified client interface that works with multiple
backends (Ollama, OpenRouter, Mock) using centralized configuration.
All model settings are read from AIModelConfiguration.
Supports automatic fallback to smaller models on rate limiting.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, List, Optional

import requests

from .ai_config import ModelConfig


@dataclass
class ModelMessage:
    """Represents a chat message sent to a language model."""

    role: str
    content: str


class UnifiedModelClient:
    """Unified client that routes to Ollama or OpenRouter based on configuration.

    This client reads from AIModelConfiguration and automatically selects
    the appropriate backend. Supports automatic fallback to smaller models
    when rate limited.

    Usage:
        config = ModelConfig(provider="ollama", model="gpt-oss:20b-cloud",
                           temperature=0.7, max_tokens=1024, fallback_model="qwen:1.7b")
        client = UnifiedModelClient(config)
        response = client.chat([ModelMessage(role="user", content="Hello")])
    """

    def __init__(self, config: ModelConfig):
        """Initialize client with model configuration.

        Args:
            config: ModelConfig specifying provider, model, temperature, etc.
        """
        self.config = config
        self._rate_limited = False
        self._fallback_used_count = 0

    def chat(
        self, messages: List[ModelMessage], tools: Optional[List[Any]] = None
    ) -> str:
        """Send a chat completion request and return the response text.

        Routes to the appropriate backend based on provider configuration.
        Automatically falls back to smaller model if rate limited.

        Args:
            messages: List of chat messages
            tools: Optional list of tool definitions (not yet implemented)

        Returns:
            Response text from the model

        Raises:
            RuntimeError: If the API call fails
        """
        # Try primary model first
        try:
            return self._make_request(self.config.model, messages)
        except RuntimeError as exc:
            # Check if this is a rate limit error
            error_msg = str(exc).lower()
            if any(
                term in error_msg
                for term in ["rate limit", "429", "too many requests", "quota exceeded"]
            ):
                if self.config.fallback_model:
                    print(
                        f"⚠ Rate limited on {self.config.model}, falling back to {self.config.fallback_model}"
                    )
                    self._rate_limited = True
                    self._fallback_used_count += 1
                    # Wait a bit before fallback
                    time.sleep(1)
                    return self._make_request(self.config.fallback_model, messages)
            # Not a rate limit error, re-raise
            raise

    def _make_request(self, model: str, messages: List[ModelMessage]) -> str:
        """Make a request to the model API.

        Args:
            model: Model name to use
            messages: List of chat messages

        Returns:
            Response text from the model

        Raises:
            RuntimeError: If the API call fails
        """
        # Prepare payload for Ollama or OpenRouter
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        headers = {"Content-Type": "application/json"}
        url = ""

        if self.config.provider == "openrouter":
            url = f"{self.config.base_url}/chat/completions"
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            # OpenRouter-specific headers
            headers["HTTP-Referer"] = "https://github.com/pptx-agent-langgraph"
            headers["X-Title"] = "PPTX Agent"
        elif self.config.provider == "ollama":
            url = f"{self.config.base_url}/chat/completions"
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

        try:
            timeout_seconds = float(os.getenv("MODEL_REQUEST_TIMEOUT_SECONDS", "120"))
            response = requests.post(
                url, json=payload, headers=headers, timeout=timeout_seconds
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Model call timed out after {timeout_seconds:g} seconds"
            )
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"Could not connect to {self.config.provider} at {url}. "
                f"Ensure the service is running. Error: {exc}"
            )
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"Model API returned error: {exc}. Response: {response.text}"
            )
        except Exception as exc:
            raise RuntimeError(f"Model call failed: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise RuntimeError(
                f"Invalid JSON response from {self.config.provider}: {response.text}"
            )

        # Handle OpenAI-compatible response format
        if "choices" in data and len(data["choices"]) > 0:
            message = data["choices"][0].get("message", {})
            return message.get("content", "")

        # Handle Ollama direct response format
        if "response" in data:
            return data["response"]

        # Fallback
        raise RuntimeError(
            f"Unexpected response format from {self.config.provider}: {data}"
        )
