from dataclasses import dataclass
import hashlib
import hmac
import secrets
import time


@dataclass(frozen=True)
class ActivatedSession:
    session_id: str
    device_id: str
    expires_at: int


class EnrollmentSessionBridge:
    """Bridge enrollment secrets into a short-lived device-bound session.

    The bridge is intentionally framework-agnostic: callers provide the existing
    session registry's issue/revoke primitives. The enrollment secret is never
    persisted in the session object.
    """

    def __init__(self, ttl_seconds: int = 900):
        self.ttl_seconds = ttl_seconds
        self._device_secrets: dict[str, bytes] = {}

    def register_enrollment_secret(self, device_id: str, secret: bytes) -> None:
        if not device_id or not secret or len(secret) < 32:
            raise ValueError("invalid enrollment secret")
        self._device_secrets[device_id] = bytes(secret)

    def _proof(self, secret: bytes, nonce: str, timestamp: int) -> str:
        msg = f"{nonce}:{timestamp}".encode()
        return hmac.new(secret, msg, hashlib.sha256).hexdigest()

    def activate(self, device_id: str, nonce: str, timestamp: int,
                 proof: str, issue_session):
        secret = self._device_secrets.get(device_id)
        if secret is None:
            raise PermissionError("device is not enrolled")
        now = int(time.time())
        if abs(now - int(timestamp)) > 90:
            raise PermissionError("stale session proof")
        expected = self._proof(secret, nonce, int(timestamp))
        if not hmac.compare_digest(expected, proof):
            raise PermissionError("invalid session proof")

        session_id, expires_at = issue_session(device_id, self.ttl_seconds)
        return ActivatedSession(session_id, device_id, int(expires_at))

    def build_proof(self, device_id: str, nonce: str, timestamp: int) -> str:
        secret = self._device_secrets.get(device_id)
        if secret is None:
            raise PermissionError("device is not enrolled")
        return self._proof(secret, nonce, int(timestamp))
