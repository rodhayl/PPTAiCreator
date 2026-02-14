"""Unit tests for event store and SSE formatting helpers."""

from src.events import EventStore, format_sse_event


def test_event_store_publish_and_filter():
    store = EventStore()

    e1 = store.publish(10, "phase_started", {"phase": "outline"})
    e2 = store.publish(10, "phase_completed", {"phase": "outline"})

    all_events = store.list_events(10)
    assert len(all_events) >= 2
    assert all_events[-2]["type"] == "phase_started"
    assert all_events[-1]["type"] == "phase_completed"

    filtered = store.list_events(10, since_ts=e1["ts"])
    assert any(event["type"] == "phase_completed" for event in filtered)

    sse = format_sse_event(e2)
    assert sse.startswith("data: ")
    assert sse.endswith("\n\n")


def test_event_store_publish_bus_failure(monkeypatch):
    store = EventStore()

    class BrokenBus:
        def publish(self, channel, payload):
            raise RuntimeError("boom")

    store._bus = BrokenBus()
    event = store.publish(1, "x", {})
    assert event["type"] == "x"


def test_event_store_trims_max_events():
    store = EventStore()
    store._max_events = 3

    for i in range(5):
        store.publish(42, f"evt_{i}", {"i": i})

    events = store.list_events(42)
    assert len(events) == 3
    assert [e["type"] for e in events] == ["evt_2", "evt_3", "evt_4"]
