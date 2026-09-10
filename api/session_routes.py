import time

from fastapi import HTTPException


def _device_secret(body: dict) -> bytes:
    value = body.get("device_secret", "")
    if not isinstance(value, str) or len(value) != 64:
        raise HTTPException(status_code=401, detail="valid device credentials are required")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="valid device credentials are required") from exc


def _authenticate_device(session_service, body: dict) -> str:
    device_id = str(body.get("device_id", ""))
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id is required")
    secret = _device_secret(body)
    if not session_service.store.verify_secret(device_id, secret):
        raise HTTPException(status_code=401, detail="invalid device credentials")
    return device_id


def _authenticate_session(session_service, body: dict) -> tuple[str, str]:
    device_id = str(body.get("device_id", ""))
    session_id = str(body.get("session_id", ""))
    if not device_id or not session_id:
        raise HTTPException(status_code=401, detail="device_id and session_id are required")
    if not session_service.store.validate_session(session_id, device_id):
        raise HTTPException(status_code=401, detail="invalid or expired session")
    return device_id, session_id


def register_session_routes(app, session_service, audit_log=None):
    def audit(event_type, device_id, session_id, detail=None):
        if audit_log:
            audit_log.record(event_type, device_id, session_id, detail or {})

    @app.post("/v1/session/create")
    def create_session(body: dict):
        device_id = _authenticate_device(session_service, body)
        try:
            result = session_service.create(device_id)
            audit("session.created", device_id, result["session_id"])
            return {"ok": True, **result}
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/v1/session/refresh")
    def refresh_session(body: dict):
        device_id = str(body.get("device_id", ""))
        token = str(body.get("refresh_token", ""))
        if not device_id or not token:
            raise HTTPException(status_code=400, detail="device_id and refresh_token are required")
        try:
            return {"ok": True, **session_service.refresh(device_id, token)}
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @app.post("/v1/session/list")
    def list_sessions(body: dict):
        device_id, session_id = _authenticate_session(session_service, body)
        include_inactive = body.get("include_inactive", False)
        if not isinstance(include_inactive, bool):
            raise HTTPException(status_code=400, detail="include_inactive must be a boolean")

        device = session_service.store.get_device(device_id)
        if not device:
            raise HTTPException(status_code=401, detail="device not found")
        sessions = session_service.store.list_sessions(
            device_id,
            include_inactive=include_inactive,
            current_session_id=session_id,
        )
        active_count = sum(1 for item in sessions if item["active"])
        return {
            "ok": True,
            "device": {
                "device_id": device["device_id"],
                "capabilities": sorted(device["capabilities"]),
                "revoked": device["revoked"],
                "created_at": int(device["created_at"]),
            },
            "summary": {
                "total": len(sessions),
                "active": active_count,
                "inactive": len(sessions) - active_count,
            },
            "sessions": sessions,
        }

    @app.post("/v1/session/revoke")
    def revoke_session(body: dict):
        device_id, session_id = _authenticate_session(session_service, body)
        target_session_id = str(body.get("target_session_id", ""))
        if not target_session_id:
            raise HTTPException(status_code=400, detail="target_session_id is required")
        target = session_service.store.get_session(target_session_id)
        if not target or target["device_id"] != device_id:
            raise HTTPException(status_code=404, detail="session not found")
        if target["revoked"] or target["expires_at"] <= int(time.time()):
            raise HTTPException(status_code=409, detail="session is already inactive")
        session_service.revoke_session(device_id, target_session_id)
        audit("session.revoked", device_id, session_id, {"target_session_id": target_session_id})
        return {
            "ok": True,
            "revoked": True,
            "session_id": target_session_id,
            "current_session": target_session_id == session_id,
        }

    @app.post("/v1/session/logout")
    def logout(body: dict):
        device_id, session_id = _authenticate_session(session_service, body)
        target_session = str(body.get("target_session_id") or session_id)
        if target_session != session_id:
            raise HTTPException(status_code=403, detail="a session can only revoke itself")
        session_service.logout(device_id, session_id)
        audit("session.logged_out", device_id, session_id)
        return {"ok": True, "logged_out": True, "session_id": session_id}

    @app.post("/v1/session/logout-device")
    def logout_device(body: dict):
        device_id = _authenticate_device(session_service, body)
        session_service.logout_device(device_id)
        audit("device.revoked", device_id, "")
        return {"ok": True, "device_revoked": True}
