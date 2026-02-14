"""Additional branch tests for storage backends."""

import builtins

import pytest

from src.state import PipelineState
from src.storage.backends import (
    NoopEventBus,
    RedisEventBus,
    SQLCheckpointStore,
    sqlite_url_from_path,
)


class BadModelDump:
    def model_dump(self):
        raise ValueError("bad")


def test_storage_serializers_and_save_guards(tmp_path):
    store = SQLCheckpointStore(sqlite_url_from_path(str(tmp_path / "db.sqlite")))

    assert store._serialize_outline(None) is None
    assert store._serialize_content(None) is None

    class BadState:
        claims = []
        evidences = []
        citations = []
        references = []

    assert store._serialize_research(BadState()) is not None
    assert store._serialize_outline(BadModelDump()) is None
    assert store._serialize_content([BadModelDump()]) is None

    state = PipelineState(user_input="topic")
    store.save_state(state)

    state.run_id = "999999"
    store.save_state(state)
    store.engine.dispose()


def test_record_complete_starts_run_when_missing(tmp_path):
    store = SQLCheckpointStore(sqlite_url_from_path(str(tmp_path / "db.sqlite")))
    state = PipelineState(user_input="topic")

    run_id = store.record_run_complete(state, output_path="", execution_time=0.1)
    assert run_id > 0
    store.engine.dispose()


def test_storage_record_log_and_list_and_details(tmp_path):
    store = SQLCheckpointStore(sqlite_url_from_path(str(tmp_path / "db.sqlite")))
    state = PipelineState(user_input="topic")
    run_id = store.start_run(state)

    store.record_log(run_id, "hello", level="INFO")

    details = store.get_run_details(run_id)
    assert details is not None
    assert details["id"] == run_id

    runs = store.list_runs(limit=5)
    assert runs
    assert runs[0]["id"] == run_id

    assert store.get_run_details(9999999) is None
    store.engine.dispose()


def test_noop_event_bus_publish():
    bus = NoopEventBus()
    assert bus.publish("chan", {"a": 1}) is None


def test_redis_event_bus_import_error(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "redis":
            raise ImportError("redis unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError):
        RedisEventBus("redis://localhost:6379/0")
