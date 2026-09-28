from __future__ import annotations

"""Opt-in guard for when the backend is reachable from the LAN (ZYRA_LAN_MODE=1).

Loopback peers (the desktop app itself) keep full access. Any other peer may
only reach the endpoints a paired phone needs; everything else, including
setup, voice and desktop-control routes, is refused before it reaches a handler.
"""

LOOPBACK = {"127.0.0.1", "::1", "localhost"}
LAN_EXACT = {
    "/health",
    "/v1/devices/pairing/enroll",
    "/v1/devices/session/activate",
    "/v1/session/create",
    "/v1/session/refresh",
    "/v1/session/list",
    "/v1/session/revoke",
    "/v1/session/logout",
    "/v1/remote/commands",
    "/v1/realtime/ws",
}
LAN_PREFIXES = ("/v1/runtime/tasks/",)


def lan_path_allowed(path: str) -> bool:
    return path in LAN_EXACT or path.startswith(LAN_PREFIXES)


class LanGuardMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            client = scope.get("client")
            peer = client[0] if client else ""
            if peer not in LOOPBACK and not lan_path_allowed(scope.get("path", "")):
                if scope["type"] == "websocket":
                    await send({"type": "websocket.close", "code": 1008})
                else:
                    await send({
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [(b"content-type", b"application/json")],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b'{"detail":"not available over the network"}',
                    })
                return
        await self.app(scope, receive, send)
