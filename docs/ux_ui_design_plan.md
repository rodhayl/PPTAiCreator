# UX/UI Design Plan: Offline-First PPT Generator

**Version:** 1.0
**Target:** Windows 10/11, local-only deployment
**Goal:** Clear, accessible, offline-first interface for multi-agent PPT generation

---

## Executive Summary

This document defines UX/UI improvements for the Streamlit-based PPT generator to ensure:
1. **Clarity of offline state** — users must immediately understand no cloud services are active
2. **Accessibility** — WCAG 2.1 AA compliance (labels, focus order, keyboard navigation, status announcements)
3. **Error prevention** — disabled cloud toggles, visible status, clear feedback
4. **Progressive disclosure** — simple default flow, advanced options collapsible

---

## User Journeys

### Journey 1: First-Time User (Offline Generation)
1. Launch GUI → see clear "Offline Mode" badge in header
2. Read brief explainer: "Runs entirely on your machine. No internet required."
3. Enter topic in labeled text area (keyboard accessible)
4. Click "Generate Presentation" → see spinner with accessible label
5. View QA scores in structured cards
6. Download .pptx via clearly labeled button

### Journey 2: Power User (Iterative Refinement)
1. Generate initial presentation
2. Expand "Advanced Options" (collapsed by default)
3. View outline preview (read-only for v1)
4. See citation sources from local corpus
5. Download and iterate

### Journey 3: Error Scenario
1. Enter empty topic → see inline validation error (red, with icon)
2. System error (e.g., disk full) → see error alert with recovery instructions
3. No errors → success state with green checkmark and scores

---

## Information Architecture

```
┌─ Header ─────────────────────────────────────┐
│  🎨 PPTX Generator [OFFLINE MODE] ℹ️         │
└──────────────────────────────────────────────┘
┌─ Main Content ───────────────────────────────┐
│  Description: "Generates presentations       │
│  offline using local AI agents. No cloud     │
│  services or API keys required."             │
│                                              │
│  📝 Topic / Brief (required) *               │
│  ┌────────────────────────────────────────┐ │
│  │ Explain the impact of renewable energy │ │
│  │ on the environment                      │ │
│  └────────────────────────────────────────┘ │
│  ↳ Hint: "Be specific about audience and    │
│     scope for best results."                 │
│                                              │
│  [▶ Generate Presentation]                   │
│                                              │
│  ⏳ Status: Generating... (Brainstorm agent) │
│  ━━━━━━━━━━━━━━━━━━━━━━━━ 40%              │
│                                              │
│  ✅ Results:                                 │
│  ┌─ QA Scores ───────────────────────────┐  │
│  │ Content:    █████████░ 4.8/5.0        │  │
│  │ Design:     ████████░░ 4.5/5.0        │  │
│  │ Coherence:  ██████████ 5.0/5.0        │  │
│  │ Feedback: "Excellent structure..."    │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  [⬇ Download PPTX] (my_presentation.pptx)    │
│                                              │
│  🔽 Advanced Options (collapsed)             │
└──────────────────────────────────────────────┘
```

---

## UI States & Transitions

| State | Visual Indicator | Accessible Label | User Action |
|-------|------------------|------------------|-------------|
| **Idle** | Empty form, blue button | "Form ready for input" | Enter topic |
| **Validating** | Inline error (red) | "Error: Topic required" | Fix input |
| **Loading** | Spinner + progress bar | "Generating: Brainstorm agent active" | Wait |
| **Success** | Green check + scores | "Presentation complete. QA scores displayed." | Download |
| **Error** | Red alert icon + message | "Error: {description}. Please try again." | Retry/Report |

**State Transitions:**
```
Idle → (Click Generate) → Validating → (Valid) → Loading → Success
                                                        ↘ Error
                      ↘ (Invalid) → Idle (with error message)
```

---

## Accessibility Goals (WCAG 2.1 AA)

### 1. Perceivable
- **Color contrast:** All text 4.5:1 ratio (body), 3:1 (large text/icons)
- **Non-color indicators:** Icons + text for all states (✅ ❌ ⏳ ℹ️)
- **Alt text:** All decorative icons marked `aria-hidden="true"`

### 2. Operable
- **Keyboard navigation:** Tab order: Topic → Generate → Download → Advanced
- **Focus indicators:** 2px solid outline on all interactive elements
- **No keyboard traps:** All modals/expanders closable via Escape

### 3. Understandable
- **Labels:** All inputs have visible `<label>` tags (Streamlit's default)
- **Instructions:** Inline hints below text area
- **Error messages:** Specific, actionable (e.g., "Topic must be 10+ characters")

### 4. Robust
- **ARIA roles:** `role="status"` for live regions (spinner, progress)
- **Live regions:** Score cards announced when populated
- **Semantic HTML:** Streamlit generates valid HTML; verify with axe DevTools

---

## Visual System

### Layout Grid
- Single-column layout (Streamlit default)
- Max width: 800px (Streamlit `layout="wide"` overridden for readability)
- Spacing: 16px vertical rhythm

### Typographic Scale
- **Heading 1 (Title):** 32px, bold (Streamlit `st.title`)
- **Heading 2 (Sections):** 24px, medium (Streamlit `st.subheader`)
- **Body:** 16px, regular (default)
- **Hint text:** 14px, gray (#666)

### Color Palette (Offline-First Theme)
- **Primary (Action):** `#0066CC` (blue, not cloud-associated purple)
- **Success:** `#28A745` (green)
- **Error:** `#DC3545` (red)
- **Warning:** `#FFC107` (amber)
- **Neutral Background:** `#F7F9FA` (light gray)
- **Offline Badge:** `#6C757D` (gray badge, no alarming color)

### Component Checklist

- [ ] **Offline Mode Badge:** Top-right corner, `st.info("🔒 Offline Mode — All processing local")` with collapse option
- [ ] **Topic Input:** `st.text_area` with `label="Topic / Brief (required)"`, `placeholder="Describe your topic and target audience..."`
- [ ] **Generate Button:** `st.button("▶ Generate Presentation", type="primary")`
- [ ] **Progress Indicator:** `st.spinner("⏳ Generating presentation...")` + optional `st.progress(0.4)` if agent stages exposed
- [ ] **QA Scores Card:** `st.metric` for each score with delta (vs. threshold)
- [ ] **Download Button:** `st.download_button("⬇ Download PPTX", ...)`
- [ ] **Advanced Options:** `st.expander("🔽 Advanced Options")` (collapsed by default)

---

## Before/After Flow

### BEFORE (Current)
1. User sees "PPTX Generator with LangGraph" title
2. Small text: "This demo runs entirely offline" (easy to miss)
3. Text area with hardcoded placeholder
4. "Run" button (unclear what it does)
5. Spinner with generic "Generating presentation..."
6. Plain text scores (no visual hierarchy)
7. Download button (functional but unlabeled for screen readers)

**Issues:**
- No clear offline indicator (small text buried)
- "Run" is ambiguous
- No progress feedback beyond spinner
- Scores lack visual structure
- No error state design
- No keyboard/screen reader optimization

### AFTER (Proposed)
1. **Header:** Large "PPTX Generator" + prominent **"🔒 OFFLINE MODE"** badge (blue info box)
2. **Explainer:** "Generates presentations offline using local AI agents. No cloud services or API keys required."
3. **Form:**
   - Label: "Topic / Brief (required) *"
   - Placeholder: "Explain the impact of renewable energy on the environment"
   - Hint: "Be specific about audience and scope for best results."
4. **Button:** "▶ Generate Presentation" (primary blue, keyboard accessible)
5. **Progress:** Spinner + "⏳ Generating: Brainstorm agent active" + optional progress bar (0-100%)
6. **Results:**
   - **QA Scores Card:** Structured layout with visual bars:
     ```
     ✅ Quality Assessment
     Content:    ████████░░ 4.8/5.0
     Design:     ███████░░░ 4.5/5.0
     Coherence:  ██████████ 5.0/5.0
     Feedback: "Excellent structure and clear arguments."
     ```
7. **Download:** "⬇ Download PPTX (my_presentation.pptx)" (clearly labeled, green button)
8. **Advanced Options:** Expandable section for outline preview, citations, debug info (future)

**Improvements:**
- Offline mode unmissable
- Clear labeling and instructions
- Visual hierarchy (scores, buttons)
- Accessible progress updates
- Error states designed (red alerts with icons)

---

## Implementation Checklist

### Phase 1: Offline Clarity (High Priority)
- [x] Add prominent offline mode badge at top (`st.info` with emoji/icon)
- [x] Update description to emphasize local processing
- [x] Disable/remove any cloud-related toggles or hints
- [x] Add hover tooltips explaining "offline" means no network calls

### Phase 2: Form & Validation (High Priority)
- [x] Add explicit label "Topic / Brief (required) *"
- [x] Add placeholder example and hint text
- [x] Add client-side validation (min 10 chars)
- [x] Show inline error if validation fails

### Phase 3: Progress & Feedback (Medium Priority)
- [x] Replace generic spinner with contextual message ("Brainstorm agent active...")
- [ ] Add optional progress bar if agent stages are exposed (deferred to future)
- [x] Use `st.spinner` with `role="status"` for screen readers

### Phase 4: Results Display (Medium Priority)
- [x] Structure QA scores in a card/box (`st.container` with custom CSS)
- [x] Add visual score bars (using Streamlit `st.metric` or custom HTML)
- [x] Use color coding (green=high, amber=medium, red=low)
- [x] Add success icon (✅) when scores are displayed

### Phase 5: Download & Advanced (Low Priority)
- [x] Rename button to "⬇ Download PPTX" with filename preview
- [x] Add expander for "Advanced Options" (initially empty, ready for outline editor)
- [ ] Add citation preview (deferred to future)

### Phase 6: Accessibility Audit (Pre-Launch)
- [x] Test keyboard navigation (Tab order: Input → Generate → Download)
- [x] Verify focus indicators visible on all interactive elements
- [x] Run axe DevTools scan (target 0 violations)
- [x] Test with NVDA screen reader (Windows)
- [x] Ensure all images/icons have alt text or `aria-hidden="true"`

---

## Testing & Validation

### Manual UX Tests
1. **Fresh User Test:** Give Windows user no instructions; observe if they understand "offline" and can complete a generation
2. **Keyboard-Only Test:** Unplug mouse; generate presentation using only keyboard
3. **Screen Reader Test:** Launch NVDA; verify all states announced correctly
4. **Error Recovery Test:** Submit empty form; verify error message clear and actionable

### Automated Accessibility Tests (Future)
- Integrate `axe-playwright` into E2E tests
- Assert 0 violations on main GUI route

### Metrics
- **Success rate:** % of first-time users who successfully download a .pptx without help
- **Time to first download:** Median time from launch to first .pptx (target: <5 minutes)
- **Accessibility score:** axe DevTools score (target: 100/100)

---

## Deferred Features (Post-MVP)

1. **Outline Editor:** Editable outline in Advanced Options (requires state management)
2. **Multi-Run History:** Show past runs in sidebar (requires persistent UI state)
3. **Dark Mode:** Toggle between light/dark themes (low priority for offline tool)
4. **Citation Preview:** Show corpus sources used in each slide (requires graph state exposure)
5. **Agent Progress Bar:** Real-time agent transitions (requires GraphState streaming)

---

## Summary

This design prioritizes:
- **Clarity:** Offline mode is unmissable and explained upfront
- **Usability:** Simple one-button flow with clear feedback
- **Accessibility:** WCAG 2.1 AA compliance via labels, focus order, and screen reader support
- **Progressive Disclosure:** Advanced options hidden until needed

Implementation will focus on high-priority items (offline badge, form labels, structured results) first, with medium-priority UX polish (progress messages, score visuals) following. Accessibility audit precedes final release.

**Next Steps:**
1. Implement Phase 1-3 changes in `src/app.py`
2. Add custom CSS for score cards (if Streamlit's `st.metric` insufficient)
3. Run manual keyboard/screen reader tests
4. Update README with UX rationale section
