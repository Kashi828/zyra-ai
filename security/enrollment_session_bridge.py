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
    """Convert a verified device proof into a short-lived session.

    The bridge deliberately does not store enrollment secrets. A caller supplies
    a verifier backed by the persistent credential store.
    """

    def __init__(self, store, ttl_seconds: int = 900, proof_ttl_seconds: int = 90):
        self.store = store
        self.ttl_seconds = int(ttl_seconds)
        self.proof_ttl_seconds = int(proof_ttl_seconds)
        self._used_nonces: dict[tuple[str, str], int] = {}

    @staticmethod
    def proof(secret: bytes, nonce: str, timestamp: int) -> str:
        if not isinstance(secret, (bytes, bytearray)) or len(secret) < 32:
            raise ValueError("invalid enrollment secret")
        message = f"{nonce}:{int(timestamp)}".encode("utf-8")
        return hmac.new(bytes(secret), message, hashlib.sha256).hexdigest()

    def activate(
        self,
        device_id: str,
        nonce: str,
        timestamp: int,
        proof: str,
        verify_proof,
    ) -> ActivatedSession:
        if not device_id or not nonce or not isinstance(proof, str):
            raise PermissionError("missing session proof")
        try:
            timestamp = int(timestamp)
        except (TypeError, ValueError) as exc:
            raise PermissionError("invalid session timestamp") from exc

        now = int(time.time())
        if abs(now - timestamp) > self.proof_ttl_seconds:
            raise PermissionError("stale session proof")

        device = self.store.get_device(device_id)
        if not device or device["revoked"]:
            raise PermissionError("device is not enrolled")

        key = (device_id, nonce)
        self._purge_nonces(now)
        if key in self._used_nonces:
            raise PermissionError("session proof already used")

        if not verify_proof(device_id, nonce, timestamp, proof):
            raise PermissionError("invalid session proof")

        self._used_nonces[key] = timestamp
        session_id = "sess_" + secrets.token_urlsafe(18)
        expires_at = self.store.issue_session(device_id, session_id, self.ttl_seconds)
        return ActivatedSession(session_id, device_id, int(expires_at))

    def _purge_nonces(self, now: int) -> None:
        cutoff = now - self.proof_ttl_seconds
        self._used_nonces = {
            key: value for key, value in self._used_nonces.items() if value >= cutoff
        }

    @classmethod
    def build_proof(cls, secret: bytes, nonce: str, timestamp: int) -> str:
        """Client-side helper; keep the secret outside the model/tool layer."""
        return cls.proof(secret, nonce, timestamp)
