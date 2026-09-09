from security.persistent_authorization_gateway import (
    PersistentAuthorizationGateway,
)


class PersistentCommandGuard:
    """Small adapter used by command bridges before executing an action."""

    def __init__(self, gateway: PersistentAuthorizationGateway):
        self.gateway = gateway

    def check(self, device_id: str, session_id: str, capability: str) -> bool:
        return self.gateway.authorize(
            device_id=device_id,
            session_id=session_id,
            capability=capability,
        ).allowed

    def require(self, device_id: str, session_id: str, capability: str) -> None:
        self.gateway.require(device_id, session_id, capability)
