# Changelog

## [v3.1 - Migration Complete] - 2025-11-05

### Migration Complete: Centralized AI Interface
- **Completed migration** from deprecated `registry.py` to centralized `ai_interface.py`
- **Removed 6 backup files** that were remnants from development process
- **Fixed test assertions** to handle flexible section title formatting
- **All 24 tests passing** (100% success rate)
- **Code audit passed:** Zero deprecated imports, zero mock LLM references
- **Production ready:** Applications verified (Streamlit GUI, FastAPI API)

### Benefits
- Single entry point for all AI calls
- Consistent error handling and response types
- Built-in fallback mechanism for rate limits
- Type-safe responses with metadata
- Automatic JSON parsing with repair logic
- Simplified testing with singleton pattern

### Breaking Changes
- **Removed**: Direct imports from `registry.py` (use `ai_interface.py` instead)
- **Removed**: Calls to `get_llm_for_agent()` (use `get_ai_interface()` instead)
- All agent code updated to mandatory new pattern

### Documentation
- **CLAUDE.md** - Mandatory development guidelines
- **MIGRATION_FINAL_REPORT.md** - Complete migration verification report
- **AI_ARCHITECTURE.md** (v3.0) - Updated system architecture

---

## [Windows-Ready Release] - 2025-11-04

### 🎯 Major Enhancements

#### Windows Developer Experience
- **Added Windows scripts** for one-command setup and execution
  - `dev.cmd` - Setup virtual environment and install dependencies
  - `run_gui.cmd` - Launch Streamlit GUI in offline mode
  - `run_api.cmd` - Launch FastAPI server
  - `test.cmd` - Run unit and integration tests
  - `e2e.cmd` - Run API E2E tests
  - `format.cmd` - Format code with ruff and black
- **PowerShell scripts** in `scripts/` directory with proper error handling
- **Automatic .env creation** with offline defaults during setup

#### Offline-First Architecture
- **Enforced offline defaults:** `MODE=offline` in all scripts and config
- **MockLLM deterministic seeding:** Stable outputs across runs (seed=42)
- **No network calls:** Validated in all test scenarios
- **LocalCorpus only:** Whoosh BM25 search, no external APIs

#### UX/UI Improvements (Streamlit GUI)
- **Prominent offline indicator:** "🔒 OFFLINE MODE" badge at top
- **Clear form labels:** "Topic / Brief (required) *" with help text
- **Input validation:** Minimum 10 characters, disabled button when invalid
- **Structured QA scores:** 3-column layout with `st.metric` components
- **Visual state indicators:** ✅ success, ❌ error, ⏳ loading, ℹ️ info
- **Enhanced download button:** Shows filename preview
- **Advanced options:** Collapsible expander for future features
- **Accessibility:** All inputs labeled, keyboard navigation supported

#### Documentation
- **Windows Quickstart section** in README.md with:
  - One-command setup instructions
  - Troubleshooting guide
  - Offline guarantee checklist
  - 5-minute verification workflow
- **UX/UI design document** (`docs/ux_ui_design_plan.md`) with:
  - User journey mapping
  - Accessibility goals (WCAG 2.1 AA)
  - Before/after flow comparison
  - 6-phase implementation checklist

### 🐛 Bug Fixes
- **Fixed citation manager bug:** Empty evidence sources now filtered out before citation marker generation
- **Path compatibility:** Changed default DB path from `./checkpoints.db` to `checkpoints.db` (Windows-friendly)
- **Artifact directory:** Changed from `examples/` to `artifacts/` as per spec

### 🔧 Configuration
- **Added `requirements.txt`** with pinned Windows-compatible dependencies
- **Updated `pyproject.toml`:**
  - Added `e2e` pytest marker
  - Updated dev script to install package in editable mode
- **Updated `.env.example`:** Removed POSIX-style path prefix

### ✅ Testing
- **All tests passing:** 8 unit/integration + 1 API E2E test (offline)
- **Determinism validated:** Two identical runs produce identical outputs
- **Acceptance tests:** 9/9 passed (see `ACCEPTANCE_TESTS_LOG.md`)

### 📦 Deliverables
1. Windows helper scripts (`.cmd` and PowerShell)
2. Pinned `requirements.txt` for reproducible installs
3. Updated README with Windows Quickstart
4. UX/UI design plan and implementation
5. Sample generated PPTX (`artifacts/sample_output.pptx`, 37KB)
6. Comprehensive acceptance test log

### 🚀 What's Next (Deferred Features)
- Editable outline preview in Advanced Options
- Citation source viewer
- Custom templates
- Slide regeneration
- Dark mode toggle
- Multi-run history in sidebar

---

**Migration Notes for Windows Users:**
- Old `make dev` → New `dev.cmd`
- Old `make run` → New `run_gui.cmd`
- Old `make api` → New `run_api.cmd`
- Old `make test` → New `test.cmd`
- Old `make e2e` → New `e2e.cmd`

Linux/macOS users can continue using the Makefile as before.
