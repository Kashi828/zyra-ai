from services.authenticated_command import CommandRequest
from services.remote_windows_bridge import RemoteWindowsBridge
from api.protected_api import authorize_request


def register_production_command_routes(app, security_context, runner=None):
    bridge = RemoteWindowsBridge(
        runner=runner,
        auth_gateway=security_context.authorization,
    )
    auth_guard = security_context.api_auth

    @app.post("/v1/remote/commands")
    def remote_command(body: dict):
        decision = authorize_request(auth_guard, body)
        if not decision.allowed:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=decision.status_code,
                detail=decision.reason,
                headers={"Retry-After": "1"} if decision.status_code == 429 else None,
            )
        request = CommandRequest(
            session_id=str(body.get("session_id", "")),
            device_id=str(body.get("device_id", "")),
            action=str(body.get("action", "")),
            payload=body.get("payload") or {},
        )
        command_id = str(body.get("command_id") or "remote")
        result = bridge.execute(request, command_id=command_id)
        return {
            "accepted": result.accepted,
            "action": result.action,
            "status": result.status,
            "message": result.message,
        }

    return bridge
