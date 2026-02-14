"""Common pytest fixtures for the PPTX agent tests."""

import pytest


@pytest.fixture(autouse=True)
def _set_env(tmp_path, monkeypatch):
    """Ensure tests run in offline mode with a temporary database."""
    # Ensure offline mode
    monkeypatch.setenv("MODE", "offline")
    monkeypatch.setenv("MODEL_REQUEST_TIMEOUT_SECONDS", "2")
    # Create a temporary checkpoints DB
    db_file = tmp_path / "checkpoints.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    yield
    # Cleanup: remove temp DB if exists
    # On Windows, SQLite files can remain locked briefly even after connections close
    if db_file.exists():
        try:
            db_file.unlink()
        except (PermissionError, OSError):
            # Ignore cleanup errors - pytest will clean up tmp_path anyway
            pass


@pytest.fixture(autouse=True)
def configure_ai_model(tmp_path, monkeypatch):
    """Configure AI model for tests.

    All tests now require real LLM providers - no mocks allowed.
    Configures for real Ollama with gpt-oss:20b-cloud.
    """
    # Configure for real Ollama
    test_config_path = tmp_path / "test_ai_config.properties"
    test_config_path.write_text("""
ai.provider=ollama
ollama.base_url=http://localhost:11434/v1
ollama.model=gpt-oss:20b-cloud
ollama.temperature=0.7
ollama.max_tokens=2048

# Agent-specific temperatures
agent.brainstorm.temperature=0.8
agent.research.temperature=0.3
agent.content.temperature=0.7
agent.qa.temperature=0.2
""".strip())

    # Override the global AI config instance
    from src.models import ai_config
    from src.models.ai_config import AIModelConfiguration

    original_instance = ai_config._config_instance
    ai_config._config_instance = AIModelConfiguration(test_config_path)

    yield

    # Restore original instance
    ai_config._config_instance = original_instance


@pytest.fixture
def sample_corpus(tmp_path, monkeypatch):
    """Create a sample corpus directory for search tests."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    file = corpus_dir / "sample.md"
    content = "---\ntitle: Sample Article\npublished_at: 2022-01-01\n---\nThis is a test document about renewable energy."
    file.write_text(content, encoding="utf-8")
    monkeypatch.setenv("MODE", "offline")
    return corpus_dir
