from dataclasses import asdict, dataclass
import json
import threading
from typing import Callable


@dataclass(frozen=True)
class RealtimeEvent:
    event_id: str
    event_type: str
    device_id: str | None
    task_id: str | None = None
    command_id: str | None = None
    transfer_id: str | None = None
    status: str | None = None
    payload: dict | None = None

    def to_dict(self):
        value = asdict(self)
        value["payload"] = value["payload"] or {}
        return value

    def to_json(self):
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)


class RealtimeEventHub:
    """Thread-safe in-process fan-out hub used by the realtime transport."""

    def __init__(self):
        self._subscribers: dict[str, set[Callable[[RealtimeEvent], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, device_id: str, callback):
        with self._lock:
            self._subscribers.setdefault(device_id, set()).add(callback)

        def unsubscribe():
            with self._lock:
                listeners = self._subscribers.get(device_id, set())
                listeners.discard(callback)
                if not listeners:
                    self._subscribers.pop(device_id, None)

        return unsubscribe

    def publish(self, event: RealtimeEvent):
        with self._lock:
            listeners = list(self._subscribers.get(event.device_id or "*", set()))
            listeners += list(self._subscribers.get("*", set()))
        for callback in listeners:
            callback(event)
