"""Pedagogical auditor agent for continuous instructional quality checks."""

from __future__ import annotations

from typing import List

from ..state import PipelineState


def _append_unique(items: List[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def run_pedagogical_auditor(state: PipelineState, phase: str) -> PipelineState:
    """Evaluate pedagogical quality at each phase and provide suggestions.

    The auditor is intentionally deterministic so it works in offline-first mode
    without requiring model inference.
    """
    suggestions = list(state.teaching_suggestions or [])
    flags = list(state.audit_flags or [])

    if phase == "outline" and state.outline:
        if not getattr(state.outline, "learning_objectives", None):
            _append_unique(
                suggestions,
                "Add at least 2 measurable learning objectives before content generation.",
            )
            _append_unique(flags, "outline_missing_learning_objectives")

        if not getattr(state.outline, "prerequisite_knowledge", None):
            _append_unique(
                suggestions,
                "Specify prerequisite knowledge to calibrate slide complexity.",
            )
            _append_unique(flags, "outline_missing_prerequisites")

    if phase == "research":
        if len(state.claims or []) == 0:
            _append_unique(
                suggestions,
                "Research phase produced no explicit claims; add verifiable claims for factual grounding.",
            )
            _append_unique(flags, "research_missing_claims")
        if len(state.evidences or []) == 0:
            _append_unique(
                suggestions,
                "Collect evidence snippets for key claims before drafting content.",
            )
            _append_unique(flags, "research_missing_evidence")

    if phase == "design":
        total_slides = len(state.content or [])
        if total_slides > 0:
            hooks = sum(
                1 for slide in state.content if getattr(slide, "engagement_hook", None)
            )
            formative = sum(
                1 for slide in state.content if getattr(slide, "formative_check", None)
            )
            if hooks < max(1, int(total_slides * 0.4)):
                _append_unique(
                    suggestions,
                    "Increase engagement hooks to maintain learner attention across the deck.",
                )
                _append_unique(flags, "design_low_engagement_hooks")
            if formative < max(1, int(total_slides * 0.3)):
                _append_unique(
                    suggestions,
                    "Add more formative checks to validate understanding during presentation.",
                )
                _append_unique(flags, "design_low_formative_checks")

    state.teaching_suggestions = suggestions
    state.audit_flags = flags
    return state
