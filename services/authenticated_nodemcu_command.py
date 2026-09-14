from dataclasses import dataclass
from typing import Any, Mapping

from core.nodemcu_command_bridge import ACTION_CAPABILITIES, NodeMCUCommandBridge
from security.persistent_authorization_gateway import PersistentAuthorizationGateway


@dataclass(frozen=True)
class AuthenticatedNodeMCUCommand:
    device_id: str
    session_id: str
    action: str
    payload: Mapping[str, Any]


class AuthenticatedNodeMCUCommandExecutor:
    """Connect the authoritative session gateway to the capability-aware NodeMCU bridge."""

    def __init__(
        self,
        gateway: PersistentAuthorizationGateway,
        bridge: NodeMCUCommandBridge,
    ):
        self.gateway = gateway
        self.bridge = bridge

    def execute(self, request: AuthenticatedNodeMCUCommand):
        capability = ACTION_CAPABILITIES.get(request.action)
        if capability is None:
            raise PermissionError("unsupported NodeMCU action")

        decision = self.gateway.authorize(
            request.device_id,
            request.session_id,
            capability,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)

        device = self.gateway.store.get_device(request.device_id)
        if not device:
            raise PermissionError("unknown device")

        return self.bridge.execute(
            request.action,
            request.payload,
            capabilities=device["capabilities"],
        )
