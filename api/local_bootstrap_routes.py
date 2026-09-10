from __future__ import annotations

import secrets

from fastapi import HTTPException, Request


DEFAULT_DESKTOP_CAPABILITIES = (
    "windows.apps",
    "windows.files.read",
    "windows.browser",
)


def register_local_bootstrap_routes(app, security_context):
    store = security_context.store
    sessions = security_context.sessions
    audit_log = getattr(app.state, "audit_log", None)

    @app.post("/v1/local/bootstrap")
    def local_bootstrap(request: Request):
        client = request.client
        host = client.host if client else ""
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise HTTPException(status_code=403, detail="local bootstrap is loopback-only")

        trusted = store.list_trusted_devices()
        if trusted:
            raise HTTPException(status_code=409, detail="local device is already initialized")

        device_id = "desktop_" + secrets.token_urlsafe(16)
        device_secret = secrets.token_bytes(32)
        store.enroll_device(device_id, device_secret, DEFAULT_DESKTOP_CAPABILITIES)
        session = sessions.create(device_id)
        if audit_log:
            audit_log.record("device.bootstrapped", device_id, session["session_id"])
        return {
            "ok": True,
            "device_id": device_id,
            "device_secret": device_secret.hex(),
            "capabilities": list(DEFAULT_DESKTOP_CAPABILITIES),
            **session,
        }
