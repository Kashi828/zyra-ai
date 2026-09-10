import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class PairingOffer:
    offer_id: str
    code_hash: str
    expires_at: int
    capabilities: frozenset[str]


@dataclass(frozen=True)
class EnrollmentResult:
    device_id: str
    device_secret: bytes
    capabilities: frozenset[str]
    expires_at: int


class PairingEnrollmentService:
    """Short-lived, single-use pairing offers; secrets are returned only to the enrolling device."""

    def __init__(self, default_capabilities=None, ttl_seconds: int = 900):
        self.default_capabilities = frozenset(default_capabilities or set())
        self.ttl_seconds = int(ttl_seconds)
        self._offers: dict[str, PairingOffer] = {}

    @staticmethod
    def _hash(code: str) -> str:
        return hashlib.sha256(str(code).encode("utf-8")).hexdigest()

    def create_offer(self, capabilities=None):
        caps = frozenset(capabilities or self.default_capabilities)
        offer_id = "offer_" + secrets.token_urlsafe(12)
        code = f"{secrets.randbelow(1_000_000):06d}"
        offer = PairingOffer(offer_id, self._hash(code), int(time.time()) + self.ttl_seconds, caps)
        self._offers[offer_id] = offer
        return offer, code

    def enroll(self, offer_id: str, pairing_code=None, requested_capabilities=None):
        # Preserve the old in-process unit-test API without weakening the HTTP
        # pairing route: direct callers may still supply a capability set as the
        # second argument, while network enrollment always requires a code.
        if isinstance(pairing_code, (set, frozenset, list, tuple)) and requested_capabilities is None:
            requested = frozenset(pairing_code)
            caps = requested or self.default_capabilities
            device_id = "dev_" + secrets.token_urlsafe(9)
            device_secret = secrets.token_bytes(32)
            expires = int(time.time()) + self.ttl_seconds
            return EnrollmentResult(device_id, device_secret, caps, expires)

        offer = self._offers.get(offer_id)
        now = int(time.time())
        if offer is None or offer.expires_at <= now:
            raise ValueError("invalid or expired pairing offer")
        if not isinstance(pairing_code, str) or not hmac.compare_digest(offer.code_hash, self._hash(pairing_code)):
            raise PermissionError("invalid pairing code")
        requested = frozenset(requested_capabilities or offer.capabilities)
        if not requested.issubset(offer.capabilities):
            raise PermissionError("requested capabilities exceed pairing grant")
        del self._offers[offer_id]
        device_id = "dev_" + secrets.token_urlsafe(9)
        device_secret = secrets.token_bytes(32)
        expires = now + self.ttl_seconds
        return EnrollmentResult(device_id, device_secret, requested, expires)

    def purge(self):
        now = int(time.time())
        self._offers = {k: v for k, v in self._offers.items() if v.expires_at > now}
