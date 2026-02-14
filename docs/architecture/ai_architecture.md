# AI Architecture & Agent Communication

**Version:** 3.0
**Date:** 2025-11-05
**Status:** ✅ Production Ready

---

## Table of Contents
1. [Overview](#overview)
2. [Centralized AI Interface](#centralized-ai-interface)
3. [AI Configuration System](#ai-configuration-system)
4. [Agent Architecture](#agent-architecture)
5. [LangGraph Implementation](#langgraph-implementation)
6. [Prompt Engineering](#prompt-engineering)
7. [Testing Strategy](#testing-strategy)
8. [Migration Guide](#migration-guide)
9. [Quick Start Guides](#quick-start-guides)

---

## Overview

This PPT Agent uses a multi-agent architecture orchestrated by LangGraph to generate professional PowerPoint presentations. The system features a **centralized AI interface** that provides a single, maintainable entry point for all model interactions.

### Key Features
- ✅ **Centralized AIInterface** - Single entry point for all AI calls
- ✅ **Standardized AIResponse** - Consistent response format across all agents
- ✅ **Multiple Provider Support**: Ollama (local), OpenRouter (cloud)
- ✅ **Automatic Fallback Handling** - Rate limit detection with fallback model
- ✅ **True LangGraph StateGraph** with conditional routing
- ✅ **Improved Structured Prompts** for all agents
- ✅ **Agent-Specific Model Overrides**
- ✅ **Comprehensive E2E Testing** with real models

---

## Centralized AI Interface

### Architecture Overview

All AI model interactions flow through a **single centralized interface** (`AIInterface`), providing consistency, maintainability, and easy testing:

```
┌─────────────────────────────────────────────────────────┐
│                      Agents                              │
│  (brainstorm, research, content, qa)                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              AIInterface (Singleton)                     │
│  • generate(prompt, agent, system_message)              │
│  • generate_with_history(messages, agent)               │
│  • get_model_info(agent)                                │
│  • reload_config()                                      │
│  • test_connection(agent)                               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           AIModelConfiguration                          │
│  • Reads ai_config.properties                           │
│  • Agent-specific overrides                             │
│  • Provider selection (ollama/openrouter)               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            UnifiedModelClient                           │
│  • HTTP client for all providers                        │
│  • Rate limit detection                                 │
│  • Automatic fallback to secondary model                │
└────────────┬────────────────────────┬───────────────────┘
             │                        │
       ┌─────▼──────┐          ┌─────▼──────────┐
       │  Ollama    │          │  OpenRouter    │
       │  (local)   │          │  (cloud)       │
       └────────────┘          └────────────────┘
```

### Using the AI Interface

**Recommended Usage** (New Code):

```python
from src.models.ai_interface import get_ai_interface

# Get the singleton instance
ai = get_ai_interface()

# Generate with agent-specific configuration
response = ai.generate(
    prompt="Explain quantum computing",
    agent="content",
    system_message="You are a technical writer"
)

print(response.content)         # The generated text
print(response.model_used)       # e.g., "gpt-oss:20b-cloud"
print(response.provider)         # e.g., "ollama"
print(response.fallback_used)    # True if fallback was used
```

**Convenience Function** (Quick Access):

```python
from src.models.ai_interface import generate_ai_response

# Simple one-liner
text = generate_ai_response(
    "Explain quantum computing",
    agent="content"
)
```

**Multi-turn Conversations**:

```python
from src.models.ai_interface import get_ai_interface

ai = get_ai_interface()

messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."},
    {"role": "user", "content": "Give me an example"}
]

response = ai.generate_with_history(messages, agent="content")
print(response.content)
```

### AIResponse Object

All AI calls return a standardized `AIResponse` object:

```python
@dataclass
class AIResponse:
    content: str                  # The generated text
    model_used: str               # Model that generated the response
    provider: str                 # Provider (ollama/openrouter)
    fallback_used: bool           # True if fallback model was used
    tokens_used: Optional[int]    # Token count (if available)
    finish_reason: Optional[str]  # Completion reason (if available)
```

### Benefits of Centralized Interface

1. **Single Source of Truth**: All AI calls go through one place
2. **Consistent Error Handling**: All exceptions wrapped in RuntimeError
3. **Easy Testing**: Mock the singleton for tests
4. **Automatic Fallback**: Rate limiting handled transparently
5. **Configuration Reloading**: Hot reload without restart
6. **Debugging**: Easy to add logging/metrics to all AI calls
7. **Provider Abstraction**: Agents don't need to know about providers

### Configuration Management

```python
# Get model information
ai = get_ai_interface()
info = ai.get_model_info(agent="brainstorm")
print(f"Using {info['model']} via {info['provider']}")

# Test connection
success, message = ai.test_connection(agent="content")
if success:
    print(f"✓ {message}")
else:
    print(f"✗ {message}")

# Reload configuration after changes
ai.reload_config()
```

---

## AI Configuration System

All AI model settings are managed through a single configuration file: `ai_config.properties`

### Configuration File (`ai_config.properties`)

**Location:** Project root (next to `README.md`)

**Structure:**
```properties
# Provider selection: ollama or openrouter
ai.provider=ollama

# Ollama configuration
ollama.base_url=http://localhost:11434/v1
ollama.model=gpt-oss:20b-cloud
ollama.fallback_model=qwen3:1.7B
ollama.temperature=0.7
ollama.max_tokens=2048

# OpenRouter configuration
openrouter.base_url=https://openrouter.ai/api/v1
openrouter.model=google/gemma-2-9b-it:free
openrouter.api_key=YOUR_API_KEY_HERE
openrouter.temperature=0.7
openrouter.max_tokens=2048

# Agent-specific overrides (optional)
agent.brainstorm.temperature=0.8
agent.research.temperature=0.3
agent.content.temperature=0.7
agent.qa.temperature=0.2
```

### Fallback Model Support

The system includes **automatic fallback** when rate limits are encountered:

**How it works:**
1. Primary model is attempted first (e.g., `gpt-oss:20b-cloud`)
2. If rate limit detected (429 error, "rate limit" in error message)
3. System automatically falls back to secondary model (e.g., `qwen3:1.7B`)
4. 1-second delay before fallback attempt
5. Fallback usage is tracked and reported in AIResponse

**Configuration:**
```properties
ollama.fallback_model=qwen3:1.7B
```

**Detection:**
```python
response = ai.generate("Your prompt", agent="content")
if response.fallback_used:
    print(f"⚠ Used fallback model: {response.model_used}")
```

### Provider Comparison

| Provider | When to Use | Pros | Cons |
|----------|------------|------|------|
| **Ollama** | Local development, privacy-sensitive | Free, private, customizable, no API costs | Requires local resources, model download |
| **OpenRouter** | Production, variety of models | Many models, no local setup, high quality | Costs money, requires internet |

---

## Agent Architecture

The system uses **5 specialized agents**, each with its own optimized prompt and temperature settings:

### Agent Pipeline

```
1. Brainstorm Agent
   ↓ (generates outline)
2. Research Agent
   ↓ (fact-checks, adds citations)
3. Content Agent
   ↓ (generates slide content)
4. Design Agent
   ↓ (assembles PPTX)
5. QA Agent
   ↓ (evaluates quality)
   └→ [Conditional: Regenerate if scores low OR Finalize]
```

### 1. Brainstorm Agent

**Role:** Analyze user input and create structured outline

**Temperature:** `0.8` (creative)

**Optimized Prompt Structure:**
```
You are a professional presentation outline generator.

**User Brief:** {user_input}

**Instructions:**
1. Extract main topic
2. Identify target audience
3. Generate 3-5 logical section headings
4. Build cohesive narrative

**Output Format (JSON):**
{
  "topic": "...",
  "audience": "...",
  "sections": [...]
}

**Example:** [detailed example provided]

Generate the outline as valid JSON:
```

### 2. Research Agent

**Role:** Extract claims, search local corpus, assign citations

**Temperature:** `0.3` (factual)

**Process:**
1. Extract claims from user input
2. Search local corpus using Whoosh BM25
3. Assign confidence scores to evidences
4. Generate citation markers `[1]`, `[2]`, etc.
5. Build references slide entries

### 3. Content Agent

**Role:** Generate detailed slide content with bullets and speaker notes

**Temperature:** `0.7` (balanced)

**Optimized Prompt Structure:**
```
You are a professional slide content writer.

**Presentation Context:**
- Topic: {topic}
- Audience: {audience}
- Section {n}/{total}: {section_title}

**Available Citations:** [1], [2], ...

**Instructions:**
1. Create clear slide title (max 10 words)
2. Write 3-5 concise bullets (max 15 words each)
3. Use action verbs and specific details
4. Write 2-3 sentences of speaker notes
5. Include relevant citations

**Output Format (JSON):**
{
  "title": "...",
  "bullets": [...],
  "speaker_notes": "...",
  "citations": [...]
}

**Example:** [detailed example]

Generate the slide content as valid JSON:
```

### 4. Design Agent

**Role:** Assemble slides into PowerPoint file

**Temperature:** N/A (no LLM used)

**Process:**
1. Use `python-pptx` to create presentation
2. Add slides with titles and bullets
3. Include speaker notes
4. Append references slide
5. Save to `artifacts/` directory

### 5. QA Agent

**Role:** Evaluate presentation quality and provide feedback

**Temperature:** `0.2` (objective)

**Optimized Prompt Structure:**
```
You are a professional presentation QA reviewer.

**Presentation Overview:**
- Topic: {topic}
- Audience: {audience}
- Slides: {num_slides}
- Titles: {slide_titles}

**Evaluation Criteria:**
1. Content Score (1-5): Informative? Specific? Cited?
2. Design Score (1-5): Clear titles? Good formatting?
3. Coherence Score (1-5): Logical flow? Complete story?

**Scoring Guide:**
- 5.0: Excellent, publication-ready
- 4.0: Good, minor improvements
- 3.0: Acceptable, some revisions
- 2.0: Below standards
- 1.0: Poor, redesign needed

**Output Format (JSON):**
{
  "content_score": 4.5,
  "design_score": 4.0,
  "coherence_score": 4.5,
  "feedback": "Specific actionable feedback..."
}

Provide your assessment as valid JSON:
```

---

## LangGraph Implementation

### True StateGraph Architecture

We now use **LangGraph's StateGraph** for proper declarative graph orchestration:

```python
from langgraph.graph import END, StateGraph

workflow = StateGraph(PipelineState)

# Add nodes
workflow.add_node("brainstorm", brainstorm_node)
workflow.add_node("research", research_node)
workflow.add_node("content", content_node)
workflow.add_node("design", design_node)
workflow.add_node("qa", qa_node)

# Linear edges
workflow.set_entry_point("brainstorm")
workflow.add_edge("brainstorm", "research")
workflow.add_edge("research", "content")
workflow.add_edge("content", "design")
workflow.add_edge("design", "qa")

# Conditional routing from QA
workflow.add_conditional_edges(
    "qa",
    should_regenerate,  # Function that checks QA scores
    {
        "regenerate": "content",  # Loop back if scores low
        "finalize": END,          # End if scores good
    },
)

graph = workflow.compile()
```

### State Management

**PipelineState** (Pydantic BaseModel):
```python
class PipelineState(BaseModel, extra=Extra.allow):
    user_input: Optional[str]
    outline: Optional[PresentationOutline]
    claims: List[Claim]
    evidences: List[Evidence]
    citations: List[str]
    content: List[SlideContent]
    qa_report: Optional[QAReport]
    pptx_path: Optional[str]
    errors: List[str]
    config: Optional[Dict[str, Any]]
```

### Conditional Routing Logic

```python
def should_regenerate(state: PipelineState) -> Literal["regenerate", "finalize"]:
    """Check QA scores to decide next action."""
    if not state.qa_report:
        return "finalize"

    threshold = 3.0
    if (state.qa_report.content_score < threshold or
        state.qa_report.design_score < threshold or
        state.qa_report.coherence_score < threshold):
        return "regenerate"  # Loop back to content node

    return "finalize"  # End workflow
```

### Two Pipeline Options

1. **Sequential Pipeline** (`run_pipeline` in `build_graph.py`):
   - Simple sequential execution
   - No conditional routing
   - Faster for testing
   - **Default** for now

2. **LangGraph Pipeline** (`run_langgraph_pipeline` in `langgraph_impl.py`):
   - True StateGraph with conditional edges
   - Can regenerate content based on QA scores
   - Better for complex workflows
   - **Available** for production use

---

## Prompt Engineering

### Prompt Design Principles

All agent prompts follow these best practices:

1. **Clear Role Definition**
   ```
   You are a professional [role]. Your task is to [specific task].
   ```

2. **Structured Context**
   ```
   **User Brief:**
   {input}

   **Presentation Context:**
   - Topic: {topic}
   - Audience: {audience}
   ```

3. **Explicit Instructions**
   ```
   **Instructions:**
   1. Do X
   2. Do Y
   3. Do Z
   ```

4. **Output Format Specification**
   ```
   **Output Format (JSON):**
   {
     "field1": "value",
     "field2": [...]
   }
   ```

5. **Concrete Examples**
   ```
   **Example:**
   Input: "..."
   Output: {...}
   ```

6. **Clear Request**
   ```
   Generate [output type] as valid JSON:
   ```

### Temperature Guidelines

| Agent | Temp | Rationale |
|-------|------|-----------|
| Brainstorm | 0.8 | Creative outline generation |
| Research | 0.3 | Factual claim extraction |
| Content | 0.7 | Balance creativity + accuracy |
| QA | 0.2 | Objective evaluation |

---

## Testing Strategy

### Test Pyramid

```
         ┌──────────────────┐
         │  E2E Tests       │  ← Real models (Ollama, OpenRouter)
         │  (2 providers)   │
         ├──────────────────┤
         │  Integration     │  ← Multi-component tests
         │  Tests (5)       │
         ├──────────────────┤
         │  Unit Tests      │  ← Individual components
         │  (8)             │
         └──────────────────┘
```

### Test Files

1. **Unit Tests** (`tests/unit/`):
   - `test_citations.py` - Citation manager
   - `test_json_repair.py` - JSON parsing logic
   - `test_schemas.py` - Pydantic models

2. **Integration Tests** (`tests/integration/`):
   - `test_checkpoint_resume.py` - SQLite persistence
   - `test_fact_check.py` - Local corpus search
   - `test_local_search.py` - Whoosh BM25
   - `test_pptx_builder.py` - PowerPoint generation

3. **E2E Tests** (`tests/e2e/`):
   - `test_real_models_e2e.py` - Real model testing
     - `TestOllamaE2E` - Ollama tests (requires `ollama serve`)
     - `TestOpenRouterE2E` - Cloud API tests (requires API key)
     - `TestConfigurationFlexibility` - Config switching
   - `test_comprehensive_agents.py` - Full agent validation

### Running Tests

```cmd
# All unit + integration tests (fast)
test.cmd

# Ollama E2E tests (requires Ollama running)
set SKIP_OLLAMA_TESTS=false
pytest tests\e2e\test_real_models_e2e.py::TestOllamaE2E -v -m ollama

# OpenRouter E2E tests (requires API key)
set SKIP_OPENROUTER_TESTS=false
set OPENROUTER_API_KEY=your_key_here
pytest tests\e2e\test_real_models_e2e.py::TestOpenRouterE2E -v -m openrouter

# Configuration flexibility tests
pytest tests\e2e\test_real_models_e2e.py::TestConfigurationFlexibility -v

# Comprehensive agent validation (requires Ollama)
pytest tests\e2e\test_comprehensive_agents.py -v

# Run all tests
pytest tests/ -v
```

---

## Migration Guide

### Migrating from registry.py to ai_interface.py

The centralized AI interface (`ai_interface.py`) is the **recommended way** to interact with AI models. The old `registry.py` is maintained for backward compatibility but is deprecated.

### Old Way (registry.py) - Deprecated

```python
from src.models.registry import get_llm_for_agent

# Get a callable for the agent
llm = get_llm_for_agent("content")

# Call it with a prompt (returns parsed JSON or raw text)
result = llm("Generate content about quantum computing")
```

**Issues with old approach:**
- Returns Any type (unpredictable)
- No metadata about model used
- No way to know if fallback was used
- Hard to test (function is created each time)
- No multi-turn conversation support

### New Way (ai_interface.py) - Recommended

```python
from src.models.ai_interface import get_ai_interface

# Get the singleton interface
ai = get_ai_interface()

# Generate with metadata
response = ai.generate(
    prompt="Generate content about quantum computing",
    agent="content"
)

# Access results
content = response.content        # The text
model = response.model_used       # Model that responded
provider = response.provider      # ollama or openrouter
fallback = response.fallback_used # True if fallback was used
```

**Benefits of new approach:**
- Typed AIResponse with metadata
- Single instance (easier to mock in tests)
- Multi-turn conversation support
- Configuration management methods
- Connection testing built-in

### Migration Examples

#### Example 1: Simple Generation

**Old:**
```python
from src.models.registry import get_llm_for_agent

llm = get_llm_for_agent("brainstorm")
outline = llm(prompt)
```

**New:**
```python
from src.models.ai_interface import generate_ai_response

outline_text = generate_ai_response(prompt, agent="brainstorm")
# OR for metadata:
from src.models.ai_interface import get_ai_interface
ai = get_ai_interface()
response = ai.generate(prompt, agent="brainstorm")
outline_text = response.content
```

#### Example 2: With System Message

**Old:**
```python
# System messages not directly supported in old approach
llm = get_llm_for_agent("content")
prompt_with_system = f"System: You are a writer\\n\\nUser: {user_prompt}"
result = llm(prompt_with_system)
```

**New:**
```python
ai = get_ai_interface()
response = ai.generate(
    prompt=user_prompt,
    agent="content",
    system_message="You are a technical writer"
)
```

#### Example 3: Checking Model Info

**Old:**
```python
from src.models.registry import get_model_info

info = get_model_info("brainstorm")
print(f"Model: {info['model']}, Provider: {info['provider']}")
```

**New:**
```python
ai = get_ai_interface()
info = ai.get_model_info("brainstorm")
print(f"Model: {info['model']}, Provider: {info['provider']}")
print(f"Fallback: {info.get('fallback_model')}")
```

#### Example 4: Testing

**Old (hard to mock):**
```python
# Tests had to mock get_llm_for_agent and return a callable
def test_agent():
    with patch('src.models.registry.get_llm_for_agent') as mock:
        mock_llm = MagicMock(return_value={"test": "data"})
        mock.return_value = mock_llm
        # Test code...
```

**New (easier to mock):**
```python
# Mock the singleton instance
def test_agent():
    with patch('src.models.ai_interface.get_ai_interface') as mock:
        mock_ai = MagicMock()
        mock_ai.generate.return_value = AIResponse(
            content="test",
            model_used="test-model",
            provider="ollama",
            fallback_used=False
        )
        mock.return_value = mock_ai
        # Test code...
```

### Backward Compatibility

**Current Status:**
- `registry.py` is **deprecated but still functional**
- All existing code using `get_llm_for_agent()` continues to work
- New code should use `ai_interface.py`
- No breaking changes in this release

**Timeline:**
- **Current release (v3.0)**: Both approaches work
- **Future release**: `registry.py` may be removed after all agents are migrated

### Checklist for Migration

- [ ] Replace `from src.models.registry import get_llm_for_agent` with `from src.models.ai_interface import get_ai_interface`
- [ ] Change `llm = get_llm_for_agent(agent)` to `ai = get_ai_interface()`
- [ ] Change `result = llm(prompt)` to `response = ai.generate(prompt, agent=agent)`
- [ ] Update to use `response.content` instead of `result`
- [ ] Add handling for `response.fallback_used` if needed
- [ ] Update tests to mock AIInterface singleton
- [ ] Test with both primary and fallback models

---

## Quick Start Guides

### Use Case 1: Local AI with Ollama

**Scenario:** Using local models for privacy and cost savings

**Prerequisites:**
1. Install Ollama: https://ollama.com/
2. Pull a model: `ollama pull llama3`
3. Start Ollama: `ollama serve`

**Configuration** (`ai_config.properties`):
```properties
ai.provider=ollama
ollama.base_url=http://localhost:11434/v1
ollama.model=gpt-oss:20b-cloud
ollama.fallback_model=qwen3:1.7B
ollama.temperature=0.7
ollama.max_tokens=2048

# Agent-specific overrides
agent.brainstorm.temperature=0.8
agent.research.temperature=0.3
agent.content.temperature=0.7
agent.qa.temperature=0.2
```

**Run:**
```cmd
run_gui.cmd
# OR
python -c "from src.graph.build_graph import run_pipeline; run_pipeline('Your topic here')"
```

**Advantages:**
- ✅ Free to use
- ✅ Private (data stays local)
- ✅ Customizable models
- ✅ No API rate limits

---

### Use Case 2: Cloud AI with OpenRouter

**Scenario:** Production use with high-quality models

**Prerequisites:**
1. Get API key: https://openrouter.ai/keys
2. Add credits or use free models

**Configuration** (`ai_config.properties`):
```properties
ai.provider=openrouter
openrouter.base_url=https://openrouter.ai/api/v1
openrouter.api_key=sk-or-v1-your-key-here
openrouter.model=google/gemma-2-9b-it:free  # Free model
# OR
# openrouter.model=anthropic/claude-3.5-sonnet  # Paid, high quality
openrouter.temperature=0.7
openrouter.max_tokens=2048
```

**Run:**
```cmd
run_gui.cmd
```

**Advantages:**
- ✅ Access to many models
- ✅ High-quality outputs
- ✅ No local setup needed
- ✅ Scalable

**Free Models Available:**
- `google/gemma-2-9b-it:free`
- `meta-llama/llama-3.2-3b-instruct:free`
- `microsoft/phi-3-medium-128k-instruct:free`

---

## Model-Specific Recommendations

### Ollama Models

| Model | Size | Use Case | Speed |
|-------|------|----------|-------|
| `llama3` | 4.7GB | General purpose, good quality | Medium |
| `mistral` | 4.1GB | Fast, decent quality | Fast |
| `phi3` | 2.2GB | Small, efficient | Very fast |
| `gemma2` | 5.4GB | Good reasoning | Medium |

**Install:** `ollama pull <model-name>`

### OpenRouter Models

| Model | Cost | Quality | Speed |
|-------|------|---------|-------|
| `google/gemma-2-9b-it:free` | Free | Good | Fast |
| `anthropic/claude-3.5-sonnet` | $3/$15 per Mtok | Excellent | Medium |
| `openai/gpt-4-turbo` | $10/$30 per Mtok | Excellent | Medium |
| `meta-llama/llama-3.2-90b-vision` | $0.3/$0.3 per Mtok | Very Good | Fast |

---

## Troubleshooting

### Issue: Tests fail with "Could not connect to Ollama"

**Solution:**
```cmd
# Start Ollama
ollama serve

# Verify Ollama is running
curl http://localhost:11434/api/tags

# OR skip Ollama tests
set SKIP_OLLAMA_TESTS=true
pytest tests\e2e\test_real_models_e2e.py -v
```

### Issue: OpenRouter returns 401 Unauthorized

**Solution:**
- Check API key is correct in `ai_config.properties`
- Verify you have credits: https://openrouter.ai/credits
- Try a free model first

### Issue: JSON parsing fails with real models

**Solution:**
- Lower temperature (more deterministic)
- Add more examples in prompt
- Use better models (Claude, GPT-4)
- Check JSON repair logic in `UnifiedModelClient`

### Issue: Rate limiting errors

**Solution:**
- Configure fallback model: `ollama.fallback_model=qwen3:1.7B`
- System automatically retries with fallback
- Check `response.fallback_used` to see if fallback was triggered
- Consider upgrading to faster/smaller fallback model

---

## Summary

### Version 3.0 Features

✅ **Centralized AI Interface** (`ai_interface.py`) - Single maintainable entry point
✅ **Standardized AIResponse** - Consistent response format with metadata
✅ **Automatic Fallback Handling** - Rate limit detection with seamless failover
✅ **Deprecation of registry.py** - Backward compatible, migration guide provided
✅ **Settings UI** - Full configuration interface in Streamlit app
✅ **Multiple provider support**: Ollama (local), OpenRouter (cloud)
✅ **Agent-specific overrides** for temperature and tokens
✅ **LangGraph StateGraph** with conditional routing
✅ **Comprehensive E2E tests** with real models
✅ **Production-ready** with clear documentation

### Key Improvements Since v2.0

1. **Maintainability**: All AI calls go through single `AIInterface`
2. **Observability**: Every response includes model info and fallback status
3. **Resilience**: Automatic fallback on rate limits
4. **User Control**: Settings UI for model/provider configuration
5. **Developer Experience**: Better testing with singleton pattern

### Migration Path

- **Current (v3.0)**: `registry.py` deprecated but functional
- **Recommended**: New code uses `ai_interface.py`
- **Future**: `registry.py` will be removed after full migration

**Next Steps:**
1. Configure your models using Settings UI (⚙️ tab)
2. Set up fallback model for resilience
3. Tune agent temperatures for your use case
4. Migrate existing code from `registry.py` to `ai_interface.py`
5. Try different providers (Ollama for local, OpenRouter for cloud)
6. Add more sophisticated conditional routing in LangGraph
