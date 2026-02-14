"""Integration tests for multi-user API orchestration and event streaming."""

from fastapi.testclient import TestClient

import src.server as server
from src.graph.build_graph import CheckpointManager
from src.state import PipelineState

app = server.app


def _fake_run_pipeline(
    user_input,
    educational_mode=False,
    template_name=None,
    session_id=None,
    approval_phases=None,
    auto_approve=True,
):
    state = PipelineState(
        user_input=user_input,
        session_id=session_id or "test-session",
        workflow_status="completed" if auto_approve else "waiting_for_approval",
        current_phase="completed" if auto_approve else "outline",
        approval_status="approved" if auto_approve else "pending",
        waiting_for_phase=None if auto_approve else "outline",
    )
    cp = CheckpointManager()
    run_id = cp.start_run(state)
    cp.save_state(state)
    state.run_id = str(run_id)
    return state


def _fake_resume_pipeline(
    run_id, approval_notes=None, auto_approve=True, approval_phases=None
):
    state = PipelineState(
        user_input="resumed",
        session_id="test-session",
        run_id=str(run_id),
        workflow_status="completed",
        current_phase="completed",
        approval_status="approved",
        approval_notes=approval_notes,
    )
    cp = CheckpointManager()
    cp.save_state(state)
    return state


def test_multiuser_sessions_and_approval_flow(monkeypatch):
    monkeypatch.setattr(server, "run_pipeline", _fake_run_pipeline)
    monkeypatch.setattr(server, "resume_pipeline", _fake_resume_pipeline)

    client = TestClient(app)

    response = client.post("/sessions", json={})
    assert response.status_code == 200
    session_a = response.json()["session_id"]

    response = client.post("/sessions", json={})
    assert response.status_code == 200
    session_b = response.json()["session_id"]

    assert session_a != session_b

    run_a = client.post(
        "/run",
        json={
            "user_input": "Explain photosynthesis for 8th grade",
            "session_id": session_a,
            "auto_approve": False,
            "approval_phases": ["outline"],
        },
    )
    assert run_a.status_code == 200
    run_a_id = run_a.json()["run_id"]
    assert run_a.json()["status"] in {"waiting_for_approval", "completed"}

    run_b = client.post(
        "/run",
        json={
            "user_input": "Teach Newton laws for high school",
            "session_id": session_b,
            "auto_approve": True,
        },
    )
    assert run_b.status_code == 200
    run_b_id = run_b.json()["run_id"]

    assert run_a_id != run_b_id

    details_a = client.get(f"/runs/{run_a_id}")
    assert details_a.status_code == 200
    assert details_a.json()["session_id"] == session_a

    details_b = client.get(f"/runs/{run_b_id}")
    assert details_b.status_code == 200
    assert details_b.json()["session_id"] == session_b

    events = client.get(f"/runs/{run_a_id}/events")
    assert events.status_code == 200
    event_types = [event["type"] for event in events.json()["events"]]
    assert event_types
    assert "run_status_cached" in event_types

    if details_a.json()["status"] == "waiting_for_approval":
        approve = client.post(f"/runs/{run_a_id}/approve", json={"notes": "Looks good"})
        assert approve.status_code == 200
        assert approve.json()["approval_status"] == "approved"


def test_sse_endpoint_available(monkeypatch):
    monkeypatch.setattr(server, "run_pipeline", _fake_run_pipeline)

    client = TestClient(app)

    run = client.post("/run", json={"user_input": "Short topic", "auto_approve": True})
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    response = client.get(f"/runs/{run_id}/events/stream?once=true")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data:" in response.text
