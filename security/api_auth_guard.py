from dataclasses import dataclass
from .persistent_device_store import PersistentDeviceStore
from .api_rate_limiter import SlidingWindowRateLimiter


@dataclass(frozen=True)
class ApiAuthDecision:
    allowed: bool
    status_code: int
    reason: str
    device_id: str = ""


class ApiAuthGuard:
    """Central API guard: rate limit + durable device/session validation."""

    def __init__(self, store: PersistentDeviceStore, limiter=None):
        self.store = store
        self.limiter = limiter or SlidingWindowRateLimiter()

    def authorize(self, device_id: str, session_id: str, key: str) -> ApiAuthDecision:
        if not key:
            return ApiAuthDecision(False, 401, "missing authentication context")
        if not self.limiter.allow(key):
            return ApiAuthDecision(False, 429, "rate limit exceeded", device_id)
        if not device_id or not session_id:
            return ApiAuthDecision(False, 401, "missing device session", device_id)
        device = self.store.get_device(device_id)
        if not device:
            return ApiAuthDecision(False, 401, "unknown device", device_id)
        if device["revoked"]:
            return ApiAuthDecision(False, 403, "device revoked", device_id)
        if not self.store.validate_session(session_id, device_id):
            return ApiAuthDecision(False, 401, "invalid or expired session", device_id)
        return ApiAuthDecision(True, 200, "authorized", device_id)
