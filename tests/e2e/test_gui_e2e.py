"""E2E tests for API-driven run lifecycle, eventing, and persistence semantics.

These tests replace the old placeholder and validate functionality required for
browser/GUI clients, while remaining deterministic in CI and offline setups.
"""

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


def test_end_to_end_run_lifecycle_and_events(monkeypatch):
    monkeypatch.setattr(server, "run_pipeline", _fake_run_pipeline)
    monkeypatch.setattr(server, "resume_pipeline", _fake_resume_pipeline)

    client = TestClient(app)

    session = client.post("/sessions", json={})
    assert session.status_code == 200
    session_id = session.json()["session_id"]

    run = client.post(
        "/run",
        json={
            "user_input": "Benefits of renewable energy for urban communities",
            "session_id": session_id,
            "auto_approve": False,
            "approval_phases": ["outline", "research", "design"],
        },
    )
    assert run.status_code == 200
    run_payload = run.json()
    run_id = run_payload["run_id"]

    details = client.get(f"/runs/{run_id}")
    assert details.status_code == 200
    details_json = details.json()
    assert details_json["session_id"] == session_id

    events = client.get(f"/runs/{run_id}/events")
    assert events.status_code == 200
    event_types = [event["type"] for event in events.json()["events"]]
    assert event_types
    assert "run_status_cached" in event_types

    if details_json["status"] == "waiting_for_approval":
        approve = client.post(f"/runs/{run_id}/approve", json={"notes": "continue"})
        assert approve.status_code == 200
        assert approve.json()["approval_status"] == "approved"


def test_event_stream_endpoint_works_for_gui_clients(monkeypatch):
    monkeypatch.setattr(server, "run_pipeline", _fake_run_pipeline)

    client = TestClient(app)
    run = client.post("/run", json={"user_input": "Water cycle", "auto_approve": True})
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    response = client.get(f"/runs/{run_id}/events/stream?once=true")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data:" in response.text
