from services.authenticated_command import CommandRequest, CommandResult, AuthenticatedCommandExecutor
from services.command_events import CommandEvent, CommandEventStream
from services.windows_command_registry import WindowsCommandRegistry
from security.persistent_authorization_gateway import PersistentAuthorizationGateway


class RemoteWindowsBridge:
    """Compatibility-preserving remote command bridge.

    New deployments should pass a PersistentAuthorizationGateway so durable
    device/session/capability authorization is authoritative. Legacy callers
    may still provide an in-memory session registry and capability map.
    """

    def __init__(
        self,
        session_registry=None,
        capabilities_by_device=None,
        runner=None,
        auth_gateway: PersistentAuthorizationGateway | None = None,
    ):
        self.registry = session_registry
        self.capabilities_by_device = capabilities_by_device or {}
        self.events = CommandEventStream()
        self.tools = WindowsCommandRegistry(runner=runner)
        self.auth_gateway = auth_gateway

    def execute(
        self,
        request: CommandRequest,
        now: int | None = None,
        command_id: str = "remote",
    ) -> CommandResult:
        self.events.publish(CommandEvent(command_id, "started", request.action, "running"))

        if self.auth_gateway is not None:
            spec = next((s for s in self.tools.specs() if s.name == request.action), None)
            if spec is None:
                result = CommandResult(False, request.action, "rejected", "unsupported action")
                self.events.publish(CommandEvent(command_id, "rejected", request.action, result.status, result.message))
                return result
            decision = self.auth_gateway.authorize(
                request.device_id, request.session_id, spec.capability
            )
            if not decision.allowed:
                result = CommandResult(False, request.action, "rejected", decision.reason)
                self.events.publish(CommandEvent(command_id, "rejected", request.action, result.status, result.message))
                return result
            try:
                message = str(self.tools.execute(
                    request.action, request.payload,
                    # Capability is already durably authorized; this local set
                    # prevents a weaker client-controlled capability path.
                    {spec.capability},
                ))
                result = CommandResult(True, request.action, "completed", message)
            except Exception:
                result = CommandResult(False, request.action, "failed", "action execution failed")
            self.events.publish(CommandEvent(
                command_id,
                "completed" if result.accepted else "failed",
                request.action,
                result.status,
                result.message,
            ))
            return result

        # Backward-compatible pre-Mission-60 path.
        if self.registry is None or not self.registry.validate(
            request.session_id, request.device_id, now=now
        ):
            result = CommandResult(False, request.action, "rejected", "invalid or expired session")
            self.events.publish(CommandEvent(command_id, "rejected", request.action, result.status, result.message))
            return result

        capabilities = self.capabilities_by_device.get(request.device_id, set())

        def handler(payload):
            return self.tools.execute(request.action, payload, capabilities)

        executor = AuthenticatedCommandExecutor(self.registry, {request.action: handler})
        result = executor.execute(request, now=now)
        self.events.publish(CommandEvent(
            command_id,
            "completed" if result.accepted else "failed",
            request.action,
            result.status,
            result.message,
        ))
        return result
