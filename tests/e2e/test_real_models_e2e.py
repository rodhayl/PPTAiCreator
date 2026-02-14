"""End-to-end tests with real AI models (Ollama and OpenRouter).

These tests use actual AI models to generate presentations and verify
the full pipeline works with real LLM responses. Configuration is managed
centrally through ai_config.properties.

All tests use Ollama with gpt-oss:20b-cloud as primary and qwen:1.7b as fallback.

Usage:
    # Test with Ollama (requires Ollama running with gpt-oss:20b-cloud)
    pytest tests/e2e/test_real_models_e2e.py -v

    # Test with OpenRouter (requires API key in ai_config.properties)
    pytest tests/e2e/test_real_models_e2e.py -v -m openrouter
"""

import json
import os
from pathlib import Path
from urllib.request import urlopen

import pytest

from src.graph.build_graph import run_pipeline
from src.graph.langgraph_impl import run_langgraph_pipeline
from src.models.ai_config import AIModelConfiguration, get_ai_config
from src.models.ai_interface import get_ai_interface


def _ollama_available() -> bool:
    try:
        with urlopen("http://localhost:11434", timeout=2) as response:
            return 200 <= response.status < 500
    except Exception:
        return False


def _detect_installed_ollama_models() -> list[str]:
    try:
        with urlopen("http://localhost:11434/api/tags", timeout=3) as response:
            if response.status != 200:
                return []
            payload = json.loads(response.read().decode("utf-8"))
            return [
                model.get("name", "")
                for model in payload.get("models", [])
                if model.get("name")
            ]
    except Exception:
        return []


def _pick_ollama_model(installed_models: list[str]) -> str | None:
    preferred = [
        "gpt-oss:20b-cloud",
        "qwen3:1.7B",
        "qwen3:1.7b",
        "llama3.2",
    ]
    for model_name in preferred:
        if model_name in installed_models:
            return model_name
    return installed_models[0] if installed_models else None


RUN_REAL_AI = os.getenv("RUN_REAL_AI_TESTS", "false").lower() == "true"


@pytest.fixture
def ensure_ollama_config(monkeypatch, tmp_path):
    """Ensure tests use Ollama configuration."""
    monkeypatch.setenv("MODEL_REQUEST_TIMEOUT_SECONDS", "120")

    installed_models = _detect_installed_ollama_models()
    primary_model = _pick_ollama_model(installed_models)
    if not primary_model:
        pytest.skip("No local Ollama models installed; skipping real Ollama E2E")

    fallback_model = "qwen3:1.7B" if "qwen3:1.7B" in installed_models else primary_model

    # Create a test-specific config with Ollama
    test_config_path = tmp_path / "test_ai_config.properties"
    test_config_path.write_text(f"""
ai.provider=ollama
ollama.base_url=http://localhost:11434/v1
ollama.model={primary_model}
ollama.fallback_model={fallback_model}
ollama.temperature=0.7
ollama.max_tokens=2048
""".strip())
    # Override config path
    from src.models import ai_config

    original_instance = ai_config._config_instance
    ai_config._config_instance = AIModelConfiguration(test_config_path)
    yield
    # Restore
    ai_config._config_instance = original_instance


@pytest.mark.e2e
@pytest.mark.real_ai
@pytest.mark.ollama
@pytest.mark.skipif(
    not RUN_REAL_AI,
    reason="Set RUN_REAL_AI_TESTS=true to run real AI integration tests",
)
@pytest.mark.skipif(
    not _ollama_available(), reason="Ollama is not reachable on localhost:11434"
)
class TestOllamaE2E:
    """E2E tests with Ollama (requires Ollama running locally)."""

    def test_ollama_connection(self, ensure_ollama_config):
        """Test Ollama connection and model availability."""
        from src.models.client import UnifiedModelClient, ModelMessage

        config = get_ai_config().get_model_config()
        client = UnifiedModelClient(config)

        # Simple chat to verify connection
        response = client.chat([ModelMessage(role="user", content="Say 'Hello'")])
        assert len(response) > 0, "Should receive response from Ollama"
        print(f"\n[SUCCESS] Ollama connection test passed: {response[:50]}...")

    def test_full_pipeline_ollama(self, ensure_ollama_config):
        """Test complete pipeline with Ollama."""
        user_input = "Benefits of electric vehicles for city transportation"

        # Run pipeline
        state = run_pipeline(user_input)

        # Verify all stages completed
        assert state.outline is not None, "Outline should be generated"
        assert state.outline.topic, "Topic should be extracted"
        assert len(state.outline.sections) >= 3, "Should have at least 3 sections"

        assert len(state.content) > 0, "Content slides should be generated"
        assert all(
            len(slide.bullets) > 0 for slide in state.content
        ), "All slides should have bullets"

        assert state.qa_report is not None, "QA report should be generated"
        assert (
            1.0 <= state.qa_report.content_score <= 5.0
        ), "Content score in valid range"
        assert 1.0 <= state.qa_report.design_score <= 5.0, "Design score in valid range"
        assert (
            1.0 <= state.qa_report.coherence_score <= 5.0
        ), "Coherence score in valid range"

        assert state.pptx_path is not None, "PPTX should be created"
        assert Path(state.pptx_path).exists(), "PPTX file should exist"

        # Log results for manual inspection
        print("\n[SUCCESS] Ollama Test Results:")
        print(f"  Topic: {state.outline.topic}")
        print(f"  Sections: {len(state.outline.sections)}")
        print(f"  Slides: {len(state.content)}")
        print(
            f"  QA Scores: Content={state.qa_report.content_score:.1f}, "
            f"Design={state.qa_report.design_score:.1f}, "
            f"Coherence={state.qa_report.coherence_score:.1f}"
        )
        # Use ASCII encoding to avoid Windows console encoding issues
        feedback_safe = state.qa_report.feedback.encode("ascii", "replace").decode(
            "ascii"
        )
        print(f"  Feedback: {feedback_safe}")

    def test_langgraph_ollama(self, ensure_ollama_config):
        """Test LangGraph with Ollama."""
        user_input = "Sustainable agriculture practices"

        state = run_langgraph_pipeline(user_input)

        assert state.outline is not None
        assert len(state.content) > 0
        assert state.qa_report is not None
        print(
            f"\n[SUCCESS] LangGraph pipeline completed with {len(state.content)} slides"
        )


@pytest.mark.e2e
@pytest.mark.real_ai
@pytest.mark.openrouter
@pytest.mark.skipif(
    (not RUN_REAL_AI) or (os.getenv("SKIP_OPENROUTER_TESTS", "true").lower() == "true"),
    reason="Set RUN_REAL_AI_TESTS=true and SKIP_OPENROUTER_TESTS=false with API key to run.",
)
class TestOpenRouterE2E:
    """E2E tests with OpenRouter cloud API."""

    @pytest.fixture(autouse=True)
    def configure_openrouter(self, monkeypatch, tmp_path):
        """Configure OpenRouter for testing."""
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        is_local_endpoint = "127.0.0.1" in base_url or "localhost" in base_url
        if not api_key and not is_local_endpoint:
            pytest.skip("OPENROUTER_API_KEY not set in environment")
        if not api_key and is_local_endpoint:
            api_key = "lmstudio-local"

        test_config_path = tmp_path / "test_ai_config.properties"
        test_config_path.write_text(f"""
ai.provider=openrouter
    openrouter.base_url={base_url}
    openrouter.model={os.getenv("OPENROUTER_MODEL", "gpt-oss-20b")}
openrouter.api_key={api_key}
openrouter.temperature=0.7
openrouter.max_tokens=2048
""".strip())
        from src.models import ai_config

        original_instance = ai_config._config_instance
        ai_config._config_instance = AIModelConfiguration(test_config_path)
        yield
        ai_config._config_instance = original_instance

    def test_full_pipeline_openrouter_free(self):
        """Test complete pipeline with OpenRouter free model (Gemma)."""
        user_input = "Impact of AI on healthcare diagnostics"

        # Run pipeline
        state = run_pipeline(user_input)

        # Verify all stages completed
        assert state.outline is not None
        assert len(state.content) > 0
        assert state.qa_report is not None
        assert state.pptx_path is not None

    def test_langgraph_openrouter(self):
        """Test LangGraph with OpenRouter."""
        user_input = "Space exploration technologies"

        state = run_langgraph_pipeline(user_input)

        assert state.outline is not None
        assert len(state.content) > 0
        assert state.qa_report is not None


@pytest.mark.e2e
@pytest.mark.real_ai
@pytest.mark.skipif(
    not RUN_REAL_AI,
    reason="Set RUN_REAL_AI_TESTS=true to run real AI integration tests",
)
class TestConfigurationFlexibility:
    """Test ability to dynamically configure models."""

    def test_switch_providers(self, ensure_ollama_config):
        """Test switching between providers."""
        # Get initial config
        ai = get_ai_interface()
        info_before = ai.get_model_info("brainstorm")
        assert info_before["provider"] == "ollama"
        print(
            f"\n[INFO] Using provider: {info_before['provider']}, model: {info_before['model']}"
        )

    def test_agent_specific_overrides(self, ensure_ollama_config, tmp_path):
        """Test agent-specific model overrides."""
        # Create config with agent overrides
        test_config_path = tmp_path / "test_ai_config_overrides.properties"
        test_config_path.write_text("""
ai.provider=ollama
ollama.base_url=http://localhost:11434/v1
ollama.model=gpt-oss:20b-cloud
ollama.fallback_model=qwen3:1.7B
agent.brainstorm.temperature=0.9
agent.qa.temperature=0.1
""".strip())

        from src.models import ai_config

        original_instance = ai_config._config_instance
        ai_config._config_instance = AIModelConfiguration(test_config_path)

        # Test agent-specific configs
        brainstorm_config = ai_config._config_instance.get_model_config("brainstorm")
        qa_config = ai_config._config_instance.get_model_config("qa")

        assert (
            brainstorm_config.temperature == 0.9
        ), "Brainstorm should use overridden temperature"
        assert qa_config.temperature == 0.1, "QA should use overridden temperature"

        print("\n[SUCCESS] Agent-specific overrides working:")
        print(f"  Brainstorm temp: {brainstorm_config.temperature}")
        print(f"  QA temp: {qa_config.temperature}")

        # Restore
        ai_config._config_instance = original_instance
