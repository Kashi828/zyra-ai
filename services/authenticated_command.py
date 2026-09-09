from dataclasses import dataclass
from security.session_registry import SessionRegistry

@dataclass(frozen=True)
class CommandRequest:
    session_id: str
    device_id: str
    action: str
    payload: dict

@dataclass(frozen=True)
class CommandResult:
    accepted: bool
    action: str
    status: str
    message: str

class AuthenticatedCommandExecutor:
    def __init__(self, registry: SessionRegistry, handlers: dict[str, callable]):
        self.registry = registry
        self.handlers = handlers

    def execute(self, request: CommandRequest, now: int | None = None) -> CommandResult:
        if not self.registry.validate(request.session_id, request.device_id, now=now):
            return CommandResult(False, request.action, "rejected", "invalid or expired session")
        handler = self.handlers.get(request.action)
        if handler is None:
            return CommandResult(False, request.action, "rejected", "unsupported action")
        try:
            message = str(handler(request.payload))
        except Exception:
            return CommandResult(False, request.action, "failed", "action execution failed")
        return CommandResult(True, request.action, "completed", message)
