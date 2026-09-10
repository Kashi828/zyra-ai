import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class PairingRequest:
    pairing_id: str
    device_id: str
    device_type: str
    endpoint: str
    code_hash: str
    expires_at: int
    consumed: bool = False


class EcosystemPairingService:
    """Short-lived, single-use pairing records; secrets are never returned by this service."""

    def __init__(self, ttl_seconds=300):
        self.ttl_seconds = int(ttl_seconds)
        self._requests = {}

    @staticmethod
    def _hash(code):
        return hashlib.sha256(str(code).encode("utf-8")).hexdigest()

    def create(self, device_id, device_type, endpoint=""):
        if not device_id or not device_type:
            raise ValueError("device_id and device_type are required")
        pairing_id = "pair_" + secrets.token_urlsafe(18)
        code = f"{secrets.randbelow(1_000_000):06d}"
        request = PairingRequest(pairing_id, device_id, device_type, endpoint,
                                 self._hash(code), int(time.time()) + self.ttl_seconds)
        self._requests[pairing_id] = request
        return request, code

    def approve(self, pairing_id, code):
        request = self._requests.get(pairing_id)
        now = int(time.time())
        if request is None or request.consumed or request.expires_at <= now:
            raise PermissionError("pairing request is invalid or expired")
        if not hmac.compare_digest(request.code_hash, self._hash(code)):
            raise PermissionError("invalid pairing code")
        approved = PairingRequest(request.pairing_id, request.device_id, request.device_type,
                                  request.endpoint, request.code_hash, request.expires_at, True)
        self._requests[pairing_id] = approved
        return approved

    def get(self, pairing_id):
        return self._requests.get(pairing_id)

    def purge(self):
        now = int(time.time())
        self._requests = {k: v for k, v in self._requests.items()
                          if v.expires_at > now and not v.consumed}
