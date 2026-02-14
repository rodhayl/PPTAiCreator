"""Coverage-focused tests for newly introduced architecture components."""

from __future__ import annotations

import builtins
import sys
from types import SimpleNamespace

import src.events as events_mod
from src.events import EventStore, sleep_seconds
from src.state import PipelineState
from src.storage.backends import RedisEventBus, SQLCheckpointStore, sqlite_url_from_path
from src.workers.preview_worker import PreviewWorker


def test_event_store_redis_paths(monkeypatch):
    monkeypatch.setattr(
        events_mod, "get_config", lambda: SimpleNamespace(redis_url="redis://example")
    )

    class FakeBus:
        def __init__(self, _url):
            self.calls = []

        def publish(self, channel, payload):
            self.calls.append((channel, payload))

    monkeypatch.setattr(events_mod, "RedisEventBus", FakeBus)
    store = EventStore()
    emitted = store.publish(99, "x", {"ok": True})

    assert emitted["run_id"] == 99
    assert emitted["payload"]["ok"] is True


def test_event_store_redis_fallback(monkeypatch):
    monkeypatch.setattr(
        events_mod, "get_config", lambda: SimpleNamespace(redis_url="redis://example")
    )

    def raise_ctor(_url):
        raise RuntimeError("no redis")

    monkeypatch.setattr(events_mod, "RedisEventBus", raise_ctor)
    store = EventStore()
    # Should not raise
    store.publish(1, "fallback")
    sleep_seconds(0)


def test_event_store_publish_exception_branch():
    store = EventStore()

    class BrokenBus:
        def publish(self, channel, payload):
            raise RuntimeError("broken")

    store._bus = BrokenBus()
    store.publish(5, "broken-branch", {})


def test_storage_error_and_missing_row_branches(tmp_path):
    store = SQLCheckpointStore(sqlite_url_from_path(str(tmp_path / "cov.sqlite")))

    assert store._serialize_outline({"x": 1}) is not None
    assert store._serialize_content([{"x": 1}]) is not None

    class RaisingState:
        @property
        def claims(self):
            raise RuntimeError("bad claims")

        @property
        def evidences(self):
            return []

        @property
        def citations(self):
            return []

        @property
        def references(self):
            return []

    assert store._serialize_research(RaisingState()) is None
    assert store.get_run_details(999999) is None

    state = PipelineState(user_input="topic")
    state.run_id = "777777"
    # missing row should no-op
    store.save_state(state, execution_time=0.0)


def test_redis_event_bus_success_publish(monkeypatch):
    class FakeRedisClient:
        def __init__(self):
            self.published = []

        def publish(self, channel, payload):
            self.published.append((channel, payload))

    class FakeRedisModule:
        client = FakeRedisClient()

        @staticmethod
        def from_url(_url, decode_responses=True):
            return FakeRedisModule.client

    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)

    bus = RedisEventBus("redis://localhost")
    bus.publish("abc", {"x": 1})

    assert FakeRedisModule.client.published
    assert FakeRedisModule.client.published[0][0] == "abc"


def test_record_complete_with_existing_run_id(tmp_path):
    store = SQLCheckpointStore(sqlite_url_from_path(str(tmp_path / "cov.sqlite")))
    state = PipelineState(user_input="topic")
    run_id = store.start_run(state)
    state.run_id = str(run_id)

    result_id = store.record_run_complete(
        state, output_path="artifact.pptx", execution_time=0.5
    )
    assert result_id == run_id


def test_preview_worker_no_pillow_branch(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    worker = PreviewWorker()
    state = PipelineState(user_input="topic")

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PIL":
            raise ImportError("missing PIL")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    result = worker.generate_previews(state)
    assert result.preview_images == {}
    assert any("Pillow" in warning for warning in result.warnings)


def test_preview_worker_wrap_and_render_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    worker = PreviewWorker(width=640, height=360)

    lines = worker._line_wrap("one two three four", max_chars=5)
    assert len(lines) >= 2
    assert worker._line_wrap("", max_chars=5) == []

    long_bullet = " ".join(["longtext"] * 40)

    state = PipelineState(
        user_input="topic",
        run_id="cov-preview",
        content=[],
    )

    class FakeFormatted:
        def __init__(self, text):
            self.text = text

    fake_slide = SimpleNamespace(
        title="Coverage Slide",
        bullets=[
            {"text": "dict bullet", "level": 0},
            FakeFormatted("formatted bullet"),
            long_bullet,
            "",
        ]
        + [long_bullet for _ in range(20)],
    )
    state.content = [fake_slide]

    result = worker.generate_previews(state)

    assert result.preview_manifest_path is not None
