from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from .config import get_config
from .storage import NoopEventBus, RedisEventBus


class EventStore:
    """In-process event store with optional Redis fan-out for multi-worker setups."""

    def __init__(self):
        config = get_config()
        self._events: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.RLock()
        self._max_events = 500

        self._bus = NoopEventBus()
        if config.redis_url:
            try:
                self._bus = RedisEventBus(config.redis_url)
            except Exception:
                self._bus = NoopEventBus()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat()

    def publish(
        self, run_id: int, event_type: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        event = {
            "run_id": run_id,
            "type": event_type,
            "ts": self._now_iso(),
            "payload": payload or {},
        }
        with self._lock:
            self._events[run_id].append(event)
            if len(self._events[run_id]) > self._max_events:
                self._events[run_id] = self._events[run_id][-self._max_events :]

        try:
            self._bus.publish(f"runs:{run_id}:events", event)
        except Exception:
            pass

        return event

    def list_events(
        self, run_id: int, since_ts: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self._lock:
            events = list(self._events.get(run_id, []))

        if not since_ts:
            return events

        return [event for event in events if event.get("ts", "") > since_ts]


EVENT_STORE = EventStore()


def format_sse_event(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"


def sleep_seconds(seconds: float) -> None:
    time.sleep(seconds)
