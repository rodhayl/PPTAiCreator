"""Additional server endpoint branch tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import src.server as server


class DummyCP:
    def __init__(self, details=None):
        self._details = details

    def get_run_details(self, run_id):
        return self._details

    def list_runs(self, limit=1):
        return [{"id": 123}]


def test_status_not_found(monkeypatch):
    monkeypatch.setattr(server, "CheckpointManager", lambda: DummyCP(details=None))
    client = TestClient(server.app)

    response = client.get("/status/404")
    assert response.status_code == 404


def test_run_details_not_found(monkeypatch):
    monkeypatch.setattr(server, "CheckpointManager", lambda: DummyCP(details=None))
    client = TestClient(server.app)

    response = client.get("/runs/404")
    assert response.status_code == 404


def test_artifact_security_and_missing(tmp_path):
    client = TestClient(server.app)

    with server._runs_lock:
        server._runs.clear()
        outside_file = tmp_path / "outside.pptx"
        outside_file.write_text("x", encoding="utf-8")
        server._runs[1] = {"pptx_path": str(outside_file)}

    forbidden = client.get("/artifact/1")
    assert forbidden.status_code in {403, 404}

    with server._runs_lock:
        server._runs[2] = {"pptx_path": str(Path("artifacts") / "missing_file.pptx")}

    missing = client.get("/artifact/2")
    assert missing.status_code == 404


def test_run_requires_input():
    client = TestClient(server.app)
    response = client.post("/run", json={})
    assert response.status_code == 400


def test_events_not_found(monkeypatch):
    monkeypatch.setattr(server, "CheckpointManager", lambda: DummyCP(details=None))
    client = TestClient(server.app)

    response = client.get("/runs/10/events")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "path", ["/runs/10/events/stream", "/runs/10/events/stream?once=true"]
)
def test_stream_not_found(monkeypatch, path):
    monkeypatch.setattr(server, "CheckpointManager", lambda: DummyCP(details=None))
    client = TestClient(server.app)

    response = client.get(path)
    assert response.status_code == 404
