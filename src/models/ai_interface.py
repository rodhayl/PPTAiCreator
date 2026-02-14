"""Centralized AI Interface for all model interactions.

This module provides a single entry point for all AI model calls throughout
the application. It abstracts away provider differences and ensures consistent
behavior across all agents.

Key Benefits:
- Single source of truth for all AI calls
- Automatic fallback handling
- Consistent error handling
- Provider-agnostic API
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .client import UnifiedModelClient, ModelMessage
from .ai_config import get_ai_config


@dataclass
class AIResponse:
    """Standardized response from AI models."""

    content: str
    model_used: str
    provider: str
    fallback_used: bool
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class AIInterface:
    """Centralized interface for all AI model interactions.

    This class provides a consistent API for calling AI models regardless
    of the underlying provider (Ollama, OpenRouter, etc.).

    Usage:
        ai = AIInterface()
        response = ai.generate("Explain quantum computing", agent="brainstorm")
        print(response.content)
    """

    def __init__(self):
        """Initialize the AI interface with current configuration."""
        self._config = get_ai_config()
        self._clients: Dict[str, UnifiedModelClient] = {}

    def _get_client(self, agent_name: Optional[str] = None) -> UnifiedModelClient:
        """Get or create a client for the specified agent.

        Args:
            agent_name: Name of the agent (for agent-specific config)

        Returns:
            UnifiedModelClient configured for the agent
        """
        cache_key = agent_name or "default"

        if cache_key not in self._clients:
            model_config = self._config.get_model_config(agent_name)
            self._clients[cache_key] = UnifiedModelClient(model_config)

        return self._clients[cache_key]

    def generate(
        self,
        prompt: str,
        agent: Optional[str] = None,
        system_message: Optional[str] = None,
        temperature_override: Optional[float] = None,
        max_tokens_override: Optional[int] = None,
    ) -> AIResponse:
        """Generate a response from the AI model.

        This is the main method that all agents should use for AI generation.

        Args:
            prompt: The user prompt to send to the model
            agent: Agent name for agent-specific configuration (brainstorm, content, etc.)
            system_message: Optional system message to prepend
            temperature_override: Override configured temperature
            max_tokens_override: Override configured max tokens

        Returns:
            AIResponse with content and metadata

        Raises:
            RuntimeError: If the AI call fails after fallback attempts
        """
        client = self._get_client(agent)

        # Build messages
        messages = []
        if system_message:
            messages.append(ModelMessage(role="system", content=system_message))
        messages.append(ModelMessage(role="user", content=prompt))

        # TODO: Apply overrides if provided
        # For now, they're handled by the config system

        try:
            # Make the API call
            content = client.chat(messages)

            # Determine if fallback was used
            fallback_used = (
                client._rate_limited if hasattr(client, "_rate_limited") else False
            )

            # Get model info
            model_used = client.config.model
            provider = client.config.provider

            return AIResponse(
                content=content,
                model_used=model_used,
                provider=provider,
                fallback_used=fallback_used,
            )

        except Exception as e:
            # Wrap all exceptions in a consistent format
            raise RuntimeError(
                f"AI generation failed for agent '{agent}': {str(e)}"
            ) from e

    def generate_with_history(
        self, messages: List[Dict[str, str]], agent: Optional[str] = None
    ) -> AIResponse:
        """Generate a response with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            agent: Agent name for agent-specific configuration

        Returns:
            AIResponse with content and metadata
        """
        client = self._get_client(agent)

        # Convert to ModelMessage objects
        model_messages = [
            ModelMessage(role=msg["role"], content=msg["content"]) for msg in messages
        ]

        try:
            content = client.chat(model_messages)

            fallback_used = (
                client._rate_limited if hasattr(client, "_rate_limited") else False
            )

            return AIResponse(
                content=content,
                model_used=client.config.model,
                provider=client.config.provider,
                fallback_used=fallback_used,
            )

        except Exception as e:
            raise RuntimeError(f"AI generation with history failed: {str(e)}") from e

    def get_model_info(self, agent: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the model being used.

        Args:
            agent: Agent name to get model info for

        Returns:
            Dictionary with model configuration details
        """
        config = self._config.get_model_config(agent)

        return {
            "provider": config.provider,
            "model": config.model,
            "fallback_model": (
                config.fallback_model if hasattr(config, "fallback_model") else None
            ),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "base_url": config.base_url,
        }

    def reload_config(self) -> None:
        """Reload configuration and clear cached clients.

        Use this after modifying ai_config.properties to pick up changes.
        """
        from .ai_config import reload_ai_config

        reload_ai_config()
        self._config = get_ai_config()
        self._clients.clear()

    def test_connection(self, agent: Optional[str] = None) -> tuple[bool, str]:
        """Test if the AI model is accessible.

        Args:
            agent: Agent name to test

        Returns:
            Tuple of (success, message)
        """
        try:
            response = self.generate(
                prompt="Say 'OK' if you can read this.", agent=agent
            )
            return True, f"Connection successful! Model: {response.model_used}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"


# Global singleton instance
_ai_interface: Optional[AIInterface] = None


def get_ai_interface() -> AIInterface:
    """Get the global AIInterface singleton.

    This is the recommended way to access the AI interface throughout
    the application.

    Returns:
        Singleton AIInterface instance

    Example:
        from src.models.ai_interface import get_ai_interface

        ai = get_ai_interface()
        response = ai.generate("Your prompt here", agent="brainstorm")
    """
    global _ai_interface
    if _ai_interface is None:
        _ai_interface = AIInterface()
    return _ai_interface


def reload_ai_interface() -> None:
    """Reload the global AI interface.

    Use this after configuration changes to force reload of all settings.
    """
    global _ai_interface
    if _ai_interface is not None:
        _ai_interface.reload_config()
    else:
        _ai_interface = AIInterface()


# Convenience function for quick access
def generate_ai_response(
    prompt: str, agent: Optional[str] = None, system_message: Optional[str] = None
) -> str:
    """Convenience function to generate an AI response.

    This is a shorthand for get_ai_interface().generate(...).content

    Args:
        prompt: The user prompt
        agent: Agent name for configuration
        system_message: Optional system message

    Returns:
        The generated text content

    Example:
        from src.models.ai_interface import generate_ai_response

        text = generate_ai_response(
            "Explain quantum computing",
            agent="content"
        )
    """
    ai = get_ai_interface()
    response = ai.generate(prompt, agent=agent, system_message=system_message)
    return response.content
