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


def register_session_routes(app, session_service):
    @app.post("/v1/session/create")
    def create_session(body: dict):
        device_id = _authenticate_device(session_service, body)
        try:
            return {"ok": True, **session_service.create(device_id)}
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

    @app.post("/v1/session/logout")
    def logout(body: dict):
        device_id = _authenticate_device(session_service, body)
        session_id = str(body.get("session_id", ""))
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        if not session_service.store.validate_session(session_id, device_id):
            raise HTTPException(status_code=401, detail="invalid or expired session")
        session_service.logout(device_id, session_id)
        return {"ok": True, "logged_out": True}

    @app.post("/v1/session/logout-device")
    def logout_device(body: dict):
        device_id = _authenticate_device(session_service, body)
        session_service.logout_device(device_id)
        return {"ok": True, "device_revoked": True}
