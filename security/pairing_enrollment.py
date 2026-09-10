import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class EnrollmentOffer:
    offer_id: str
    code_hash: str
    capabilities: frozenset[str]
    expires_at: int
    consumed: bool = False


@dataclass(frozen=True)
class EnrollmentResult:
    device_id: str
    device_secret: bytes
    capabilities: frozenset[str]
    expires_at: int


class PairingEnrollmentService:
    """Short-lived, single-use bootstrap offers for first-time devices."""

    def __init__(self, default_capabilities=None, ttl_seconds: int = 300):
        self.default_capabilities = frozenset(default_capabilities or set())
        self.ttl_seconds = max(60, int(ttl_seconds))
        self._offers: dict[str, EnrollmentOffer] = {}

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("ascii")).hexdigest()

    def create_offer(self, capabilities=None) -> tuple[EnrollmentOffer, str]:
        caps = frozenset(
            capabilities if capabilities is not None else self.default_capabilities
        )
        offer_id = "offer_" + secrets.token_urlsafe(18)
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = int(time.time()) + self.ttl_seconds
        offer = EnrollmentOffer(
            offer_id=offer_id,
            code_hash=self._hash_code(code),
            capabilities=caps,
            expires_at=expires_at,
        )
        self._offers[offer_id] = offer
        return offer, code

    def enroll(self, offer_id: str, code: str, requested_capabilities=None):
        if (
            not offer_id
            or not isinstance(code, str)
            or len(code) != 6
            or not code.isdigit()
        ):
            raise ValueError("invalid pairing offer")

        offer = self._offers.get(offer_id)
        if offer is None or offer.consumed or offer.expires_at <= int(time.time()):
            raise ValueError("invalid or expired pairing offer")
        if not hmac.compare_digest(self._hash_code(code), offer.code_hash):
            raise ValueError("invalid pairing code")

        requested = frozenset(
            requested_capabilities
            if requested_capabilities is not None
            else offer.capabilities
        )
        if not requested.issubset(offer.capabilities):
            raise PermissionError("requested capability exceeds pairing grant")

        self._offers[offer_id] = EnrollmentOffer(
            offer_id=offer.offer_id,
            code_hash=offer.code_hash,
            capabilities=offer.capabilities,
            expires_at=offer.expires_at,
            consumed=True,
        )
        return EnrollmentResult(
            device_id="dev_" + secrets.token_urlsafe(9),
            device_secret=secrets.token_bytes(32),
            capabilities=requested,
            expires_at=offer.expires_at,
        )

    def purge(self) -> None:
        now = int(time.time())
        self._offers = {
            key: value
            for key, value in self._offers.items()
            if not value.consumed and value.expires_at > now
        }
