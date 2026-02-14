"""Unit tests for pedagogical auditor agent."""

from src.agents.pedagogical_auditor import _append_unique, run_pedagogical_auditor
from src.schemas import LearningObjective, PresentationOutline, SlideContent
from src.state import PipelineState


def test_pedagogical_auditor_all_phases():
    state = PipelineState(user_input="topic")
    state.outline = PresentationOutline(topic="T", audience="A", sections=["S1", "S2"])

    state = run_pedagogical_auditor(state, phase="outline")
    assert state.teaching_suggestions
    assert state.audit_flags

    state = run_pedagogical_auditor(state, phase="research")
    assert any("research" in flag for flag in state.audit_flags)

    state.content = [
        SlideContent(title="s1", bullets=["b1"]),
        SlideContent(title="s2", bullets=["b1"], engagement_hook="hook"),
    ]
    state = run_pedagogical_auditor(state, phase="design")
    assert any("formative" in flag for flag in state.audit_flags)


def test_pedagogical_auditor_design_low_engagement_and_formative():
    state = PipelineState(user_input="topic")
    state.content = [
        SlideContent(title="s1", bullets=["b1"]),
        SlideContent(title="s2", bullets=["b2"]),
        SlideContent(title="s3", bullets=["b3"]),
    ]

    state = run_pedagogical_auditor(state, phase="design")
    assert "design_low_engagement_hooks" in state.audit_flags
    assert "design_low_formative_checks" in state.audit_flags


def test_append_unique_skips_empty_and_duplicates():
    items = []
    _append_unique(items, "x")
    _append_unique(items, "x")
    _append_unique(items, "")
    assert items == ["x"]


def test_pedagogical_auditor_complete_inputs_adds_no_flags():
    state = PipelineState(user_input="topic")
    state.outline = PresentationOutline(
        topic="T",
        audience="A",
        sections=["S1", "S2"],
        learning_objectives=[
            LearningObjective(objective="obj1", bloom_level="understand"),
            LearningObjective(objective="obj2", bloom_level="apply"),
        ],
        prerequisite_knowledge=["pre"],
    )
    state.claims = ["c1"]
    state.evidences = ["e1"]
    state.content = [
        SlideContent(
            title="s1", bullets=["b1"], engagement_hook="h1", formative_check="f1"
        ),
        SlideContent(
            title="s2", bullets=["b2"], engagement_hook="h2", formative_check="f2"
        ),
    ]

    state = run_pedagogical_auditor(state, phase="outline")
    state = run_pedagogical_auditor(state, phase="research")
    state = run_pedagogical_auditor(state, phase="design")
    state = run_pedagogical_auditor(state, phase="other")

    assert "outline_missing_learning_objectives" not in state.audit_flags
    assert "outline_missing_prerequisites" not in state.audit_flags
    assert "research_missing_claims" not in state.audit_flags
    assert "research_missing_evidence" not in state.audit_flags
    assert "design_low_engagement_hooks" not in state.audit_flags
    assert "design_low_formative_checks" not in state.audit_flags


def test_pedagogical_auditor_outline_missing_and_design_empty_noop():
    state = PipelineState(user_input="topic")
    state = run_pedagogical_auditor(state, phase="outline")
    state = run_pedagogical_auditor(state, phase="design")
    assert isinstance(state.audit_flags, list)
