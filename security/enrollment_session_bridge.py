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
    """Bridge an enrolled device proof into a short-lived session.

    Enrollment secrets remain outside the session object. Proofs are bound to a
    one-time nonce and a short timestamp window to reduce replay risk.
    """

    def __init__(self, store, ttl_seconds: int = 900, proof_ttl_seconds: int = 90):
        self.store = store
        self.ttl_seconds = int(ttl_seconds)
        self.proof_ttl_seconds = int(proof_ttl_seconds)
        self._used_nonces: dict[tuple[str, str], int] = {}

    @staticmethod
    def _proof(secret: bytes, nonce: str, timestamp: int) -> str:
        message = f"{nonce}:{int(timestamp)}".encode("utf-8")
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    @staticmethod
    def _validate_secret(secret: bytes) -> bytes:
        if not isinstance(secret, (bytes, bytearray)) or len(secret) < 32:
            raise ValueError("invalid enrollment secret")
        return bytes(secret)

    def activate(self, device_id: str, nonce: str, timestamp: int, proof: str):
        if not device_id or not nonce or not proof:
            raise PermissionError("missing session proof")
        try:
            timestamp = int(timestamp)
        except (TypeError, ValueError) as exc:
            raise PermissionError("invalid session timestamp") from exc
        now = int(time.time())
        if abs(now - timestamp) > self.proof_ttl_seconds:
            raise PermissionError("stale session proof")

        # The persistent store is authoritative; no long-lived secret cache is
        # kept in this bridge.
        device = self.store.get_device(device_id)
        if not device or device["revoked"]:
            raise PermissionError("device is not enrolled")

        # The proof is verified against the enrollment secret only through the
        # supplied verifier. The bridge never accepts a secret from the caller.
        secret = getattr(self.store, "get_secret_for_verification", None)
        if secret is None:
            raise PermissionError("device proof verification is unavailable")
        expected_secret = secret(device_id)
        expected = self._proof(self._validate_secret(expected_secret), nonce, timestamp)
        if not hmac.compare_digest(expected, proof):
            raise PermissionError("invalid session proof")

        key = (device_id, nonce)
        self._purge_nonces(now)
        if key in self._used_nonces:
            raise PermissionError("session proof already used")
        self._used_nonces[key] = timestamp

        session_id = "sess_" + secrets.token_urlsafe(18)
        expires_at = self.store.issue_session(device_id, session_id, self.ttl_seconds)
        return ActivatedSession(session_id, device_id, int(expires_at))

    def _purge_nonces(self, now: int) -> None:
        cutoff = now - self.proof_ttl_seconds
        self._used_nonces = {
            key: value for key, value in self._used_nonces.items() if value >= cutoff
        }

    def build_proof(self, secret: bytes, nonce: str, timestamp: int) -> str:
        """Client-side helper; callers must keep the secret outside the model layer."""
        return self._proof(self._validate_secret(secret), nonce, int(timestamp))
