import time
from collections import deque
from threading import RLock


class SlidingWindowRateLimiter:
    """In-process bounded sliding-window limiter for API protection."""

    def __init__(self, limit=60, window_seconds=60):
        if limit < 1 or window_seconds <= 0:
            raise ValueError("invalid rate limit")
        self.limit = int(limit)
        self.window_seconds = int(window_seconds)
        self._events = {}
        self._lock = RLock()

    def allow(self, key: str, now=None) -> bool:
        now = time.time() if now is None else float(now)
        with self._lock:
            q = self._events.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True

    def retry_after(self, key: str, now=None) -> int:
        now = time.time() if now is None else float(now)
        with self._lock:
            q = self._events.get(key)
            if not q:
                return 0
            cutoff = now - self.window_seconds
            while q and q[0] <= cutoff:
                q.popleft()
            if not q:
                return 0
            return max(1, int(q[0] + self.window_seconds - now))
