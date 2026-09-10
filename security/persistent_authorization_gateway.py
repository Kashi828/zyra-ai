from dataclasses import dataclass
from .persistent_device_store import PersistentDeviceStore
from .emergency_stop import EmergencyStop


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    device_id: str
    session_id: str
    capability: str


class PersistentAuthorizationGateway:
    """Authoritative durable session + capability check for device actions."""

    def __init__(self, store: PersistentDeviceStore, emergency_stop: EmergencyStop | None = None):
        self.store = store
        self.emergency_stop = emergency_stop

    def authorize(self, device_id: str, session_id: str, capability: str) -> AuthorizationDecision:
        if self.emergency_stop is not None and not self.emergency_stop.allows():
            return AuthorizationDecision(
                False, "ZYRA emergency stop is engaged", device_id, session_id, capability
            )
        if not device_id or not session_id or not capability:
            return AuthorizationDecision(
                False, "missing authorization context", device_id, session_id, capability
            )

        device = self.store.get_device(device_id)
        if not device:
            return AuthorizationDecision(
                False, "unknown device", device_id, session_id, capability
            )
        if device["revoked"]:
            return AuthorizationDecision(
                False, "device is revoked", device_id, session_id, capability
            )
        if not self.store.validate_session(session_id, device_id):
            return AuthorizationDecision(
                False, "session is invalid or expired", device_id, session_id, capability
            )
        if capability not in device["capabilities"]:
            return AuthorizationDecision(
                False, "capability is not granted to device", device_id, session_id, capability
            )

        return AuthorizationDecision(True, "authorized", device_id, session_id, capability)

    def require(self, device_id: str, session_id: str, capability: str) -> None:
        decision = self.authorize(device_id, session_id, capability)
        if not decision.allowed:
            raise PermissionError(decision.reason)
