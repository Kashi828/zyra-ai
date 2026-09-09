from dataclasses import dataclass
from security.persistent_authorization_gateway import PersistentAuthorizationGateway
from .windows_command_registry import WindowsCommandRegistry


@dataclass(frozen=True)
class AuthorizedRemoteCommand:
    device_id: str
    session_id: str
    action: str
    payload: dict


class AuthorizedRemoteCommandExecutor:
    def __init__(self, registry: WindowsCommandRegistry, gateway: PersistentAuthorizationGateway):
        self.registry = registry
        self.gateway = gateway

    def execute(self, request: AuthorizedRemoteCommand):
        spec = self.registry.get(request.action)
        if spec is None:
            raise PermissionError("action is not registered")

        # The backend decides the capability; clients cannot choose a weaker check.
        self.gateway.require(request.device_id, request.session_id, spec.capability)
        return self.registry.execute(request.action, request.payload)
