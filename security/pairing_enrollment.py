import secrets
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

@dataclass(frozen=True)
class EnrollmentResult:
    device_id: str
    device_secret: bytes
    capabilities: frozenset[str]
    expires_at: int

class PairingEnrollmentService:
    def __init__(self, default_capabilities=None, ttl_seconds: int = 900):
        self.default_capabilities = frozenset(default_capabilities or set())
        self.ttl_seconds = ttl_seconds
        self._used_offers = set()

    def enroll(self, offer_id: str, requested_capabilities=None):
        if not offer_id or offer_id in self._used_offers:
            raise ValueError("invalid or already-used pairing offer")
        self._used_offers.add(offer_id)
        caps = frozenset(requested_capabilities or self.default_capabilities)
        device_id = "dev_" + secrets.token_urlsafe(9)
        device_secret = secrets.token_bytes(32)
        expires = int((datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds)).timestamp())
        return EnrollmentResult(device_id, device_secret, caps, expires)
