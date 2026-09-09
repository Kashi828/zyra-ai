import time
from dataclasses import dataclass
from threading import RLock

@dataclass
class ActiveSession:
    session_id: str
    device_id: str
    issued_at: int
    expires_at: int
    mac: str
    revoked: bool = False

    def active(self, now: int | None = None) -> bool:
        now = int(time.time()) if now is None else int(now)
        return (not self.revoked) and now < self.expires_at


class SessionRegistry:
    def __init__(self):
        self._sessions: dict[str, ActiveSession] = {}
        self._lock = RLock()

    def register(self, session: ActiveSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session

    def revoke(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.revoked = True
            return True

    def get(self, session_id: str) -> ActiveSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def validate(self, session_id: str, device_id: str, now: int | None = None) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            return session.device_id == device_id and session.active(now)
