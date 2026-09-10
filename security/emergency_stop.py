from dataclasses import dataclass
import threading
import time


@dataclass(frozen=True)
class StopState:
    stopped: bool
    changed_at: int
    reason: str


class EmergencyStop:
    """Process-local fail-closed stop gate for agent actions."""

    def __init__(self):
        self._lock = threading.RLock()
        self._state = StopState(False, int(time.time()), "")

    def engage(self, reason: str = "manual emergency stop") -> StopState:
        with self._lock:
            self._state = StopState(True, int(time.time()), str(reason)[:256])
            return self._state

    def release(self) -> StopState:
        with self._lock:
            self._state = StopState(False, int(time.time()), "")
            return self._state

    def snapshot(self) -> StopState:
        with self._lock:
            return self._state

    def require_running(self) -> None:
        if self.snapshot().stopped:
            raise PermissionError("ZYRA emergency stop is engaged")

    def allows(self) -> bool:
        return not self.snapshot().stopped
