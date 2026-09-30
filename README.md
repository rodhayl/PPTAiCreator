# PPTAgent: Staged PowerPoint Generation

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20PowerShell-informational)
![License](https://img.shields.io/badge/license-MIT-green)

**Status:** v0.1.0 source project with unit, integration and optional real-model tests. Local validation commands are documented below; current results are not published through GitHub Actions.

PPTAgent (in the `PPTAiCreator` repository) turns a presentation brief into a PowerPoint deck through outline, research, content, design and quality-review stages. It provides a Streamlit interface and FastAPI endpoints, with persisted run state and optional human approval between stages. Local/offline execution and configurable language-model integrations make it a practical project in workflow orchestration, document generation and applied AI.

## What this project demonstrates

- Explicit pipeline stages with pause/resume approval and an event timeline.
- SQLite-backed checkpoints, a GUI and API access to the same run lifecycle.
- PowerPoint generation with `python-pptx`, templates and inspectable artifacts.
- Tests that separate orchestration logic from optional real-model behavior.

Local fallback execution is different from real-model generation. Remote providers require network access and may charge for requests. Quality-review and fact-check stages support inspection; review generated content, sources and slide layout before use.

## Quickstart

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_gui.ps1
```

For API mode instead of GUI:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_api.ps1
```

API docs: `http://127.0.0.1:8000/docs`

## Core capabilities

- End-to-end presentation pipeline: `outline -> research -> content -> design -> qa`
- Dual orchestration paths:
  - standard pipeline (`src/graph/build_graph.py`)
  - LangGraph pipeline (`src/graph/langgraph_impl.py`)
- Human-in-the-loop approval and resume support by phase
- Run persistence and retrieval via SQLite-backed checkpoint storage
- Event timeline support for GUI/API clients (`/runs/{id}/events`, SSE stream)
- Built-in template system (default/professional/academic/creative/minimalist)
- Educational mode (learning objectives, pedagogical helpers, educational QA signals)
- Local retrieval/fact-check support (Whoosh, optional semantic retrieval)
- Preview/image worker support for generated slides

## Interfaces

- **GUI (Streamlit):** prompt-driven generation, settings, run history, template controls
- **API (FastAPI):** automation-friendly endpoints for sessions, run lifecycle, approvals, events, and artifacts

## Prerequisites

- Python 3.11+
- Windows PowerShell (project scripts are PowerShell-first)
- Optional for real-model testing:
  - LM Studio with OpenAI-compatible endpoint (`http://127.0.0.1:1234/v1`)
  - or other OpenRouter-compatible endpoint

## Setup (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

This creates `.venv`, installs dependencies, and installs the package in editable mode.

## Validation scope

The repository includes unit, integration, API and browser test suites. Some tests use simulated pipeline phases; real-model tests require a configured provider. The commands below are reproducible entry points, not a claim that every check passes in every environment.

When sharing a result, record the commit, command, environment, provider and scope. A test file named `enterprise_e2e` describes a scenario, not an enterprise certification.

## Run locally

### GUI

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_gui.ps1
```

### API

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_api.ps1
```

API docs are available at: `http://127.0.0.1:8000/docs`

## Quality gates and testing

### Lint/format checks

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m black --check .
```

### Main tests (unit + integration)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

### API-focused E2E

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\e2e.ps1
```

### Browser E2E (Playwright)

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest tests\e2e\test_playwright_enterprise_e2e.py -q
```

## LM Studio real-model validation

Reusable validator script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_lmstudio.ps1
```

Optional parameters:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_lmstudio.ps1 -BaseUrl "http://127.0.0.1:1234/v1" -Model "gpt-oss-20b"
```

What it verifies:
- LM Studio endpoint reachability and model listing
- Real-model `TestOpenRouterE2E::test_full_pipeline_openrouter_free`
- Real-model `TestOpenRouterE2E::test_langgraph_openrouter`

## API essentials

- `POST /sessions` -> create session
- `POST /run` -> start run (`user_input` required)
- `GET /status/{run_id}` -> status summary
- `GET /runs/{run_id}` -> full run details
- `POST /runs/{run_id}/approve` -> resume HITL run
- `GET /runs/{run_id}/events` -> event list
- `GET /runs/{run_id}/events/stream` -> SSE events
- `GET /artifact/{run_id}` -> download generated PPTX

## Repository layout

- `src/` application code (agents, graph, API, GUI, tools, storage, workers)
- `tests/` unit, integration, and e2e suites
- `scripts/` automation scripts for setup/run/test/validation
- `templates/` bundled presentation templates
- `docs/` active project documentation
- `examples/` sample inputs/assets

## Notes for GitHub publishing

- Root-level wrapper clutter and obsolete artifacts have been removed.
- Project is now PowerShell-script-first for local operations.
- Runtime/generated assets remain excluded from source control via `.gitignore`.

## Release checklist

- Run setup: `powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1`
- Run quality gates:
  - `python -m ruff check .`
  - `python -m black --check .`
  - `python -m pytest tests\unit -q`
  - `python -m pytest tests\integration -q`
  - `python -m build`
- Optional real-model validation (LM Studio):
  - `powershell -ExecutionPolicy Bypass -File .\scripts\validate_lmstudio.ps1`
- Confirm clean state before push:
  - `git status --short`
