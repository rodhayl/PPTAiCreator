"""Unit tests for human-in-the-loop orchestration pause/resume."""

from src.graph import build_graph as bg
from src.schemas import PresentationOutline, QAReport, SlideContent


def test_pipeline_pauses_and_resumes(monkeypatch, tmp_path):
    db_path = tmp_path / "checkpoints.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("CHECKPOINT_BACKEND", "sqlite")

    def fake_outline(state):
        state.outline = PresentationOutline(
            topic="Topic",
            audience="Teachers",
            sections=["Intro", "Body"],
        )
        return state

    def fake_research(state):
        return state

    def fake_content(state):
        state.content = [SlideContent(title="Intro", bullets=["Point A", "Point B"])]
        return state

    def fake_design(state):
        state.pptx_path = str(tmp_path / "deck.pptx")
        return state

    def fake_qa(state):
        state.qa_report = QAReport(
            content_score=4.0, design_score=4.0, coherence_score=4.0
        )
        return state

    monkeypatch.setattr(
        bg,
        "PHASE_PLAN",
        [
            ("outline", fake_outline),
            ("research", fake_research),
            ("content", fake_content),
            ("design", fake_design),
            ("qa", fake_qa),
        ],
    )

    paused_state = bg.run_pipeline(
        "test topic",
        approval_phases={"outline"},
        auto_approve=False,
    )

    assert paused_state.workflow_status == "waiting_for_approval"
    assert paused_state.waiting_for_phase == "outline"
    assert paused_state.approval_status == "pending"
    assert paused_state.run_id is not None

    resumed_state = bg.resume_pipeline(
        int(paused_state.run_id), approval_notes="approved"
    )

    assert resumed_state.workflow_status == "completed"
    assert resumed_state.approval_status == "approved"
    assert resumed_state.current_phase == "completed"
    assert resumed_state.qa_report is not None
