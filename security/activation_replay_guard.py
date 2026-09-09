import time


class ActivationReplayGuard:
    def __init__(self, ttl_seconds: int = 120):
        self.ttl_seconds = ttl_seconds
        self._seen: dict[tuple[str, str], int] = {}

    def accept(self, device_id: str, nonce: str, timestamp: int) -> bool:
        now = int(time.time())
        self._prune(now)
        key = (device_id, nonce)
        if key in self._seen:
            return False
        if abs(now - int(timestamp)) > self.ttl_seconds:
            return False
        self._seen[key] = now
        return True

    def _prune(self, now: int) -> None:
        cutoff = now - self.ttl_seconds
        self._seen = {k: v for k, v in self._seen.items() if v >= cutoff}
